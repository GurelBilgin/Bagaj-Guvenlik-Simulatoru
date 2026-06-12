"""Tkinter arayüzü ve X-ray dedektör animasyonu."""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from constants import YASAKLI_ESYALAR
from passenger import Passenger
from simulator import BaggageSecuritySimulator, ScanResult
from sound_utils import sonuc_sesi_cal


class AutoScrollbar(ttk.Scrollbar):
    """Gerekmediğinde kendini gizleyen kaydırma çubuğu."""

    def set(self, first: str, last: str) -> None:  # type: ignore[override]
        if float(first) <= 0.0 and float(last) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        super().set(first, last)



class BagajGuvenlikApp(tk.Tk):
    """Bagaj Güvenlik Simülatörü ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Bagaj Güvenlik Simülatörü")
        # Program açılışta ekranı dolduracak şekilde başlatılır.
        # Kullanıcı pencere moduna aldığında ise içerik sıkışmak yerine
        # kaydırılabilir ve yeniden ölçeklenen bir düzende kalır.
        self.geometry("1280x820")
        self.minsize(900, 600)
        self.configure(bg="#f4f6f8")

        self.simulator = BaggageSecuritySimulator()
        self.simulasyon_calisiyor = False
        self.proje_dizini = Path(__file__).resolve().parent
        self.reports_dir = self.proje_dizini / "reports"
        self._pencere_ikonunu_ayarla()

        self.base_canvas_width = 760
        self.canvas_width = self.base_canvas_width
        self.canvas_height = 260
        self._minimum_icerik_genisligi = 1080
        self._ana_window_id: int | None = None
        self._animasyon_step = 0
        self._animasyon_max_step = 30
        self._aktif_result: ScanResult | None = None
        self._bagaj_items: list[int] = []
        self._dinamik_canvas_items: list[int] = []
        self._canvas_resize_job: str | None = None

        self._stil_ayarla()
        self._arayuz_olustur()
        self._xray_sahnesini_ciz()
        self._kara_liste_panel_guncelle()
        self._sayac_panel_guncelle()
        self._loglari_guncelle()
        self._log_yaz("Hoş geldiniz. Demo veri yükleyip simülasyonu başlatabilirsiniz.")
        self.after(120, self._baslangic_tam_ekran_yap)
        self.bind("<F11>", self._tam_ekran_degistir)
        self.bind("<Escape>", self._tam_ekrandan_cik)

    def _pencere_ikonunu_ayarla(self) -> None:
        """Pencere ikonunu assets klasöründeki özel ikonla değiştirir."""
        icon_path = self.proje_dizini / "assets" / "icon.ico"
        png_path = self.proje_dizini / "assets" / "icon.png"

        # Windows için en sorunsuz yöntem .ico dosyasını iconbitmap ile vermektir.
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except tk.TclError:
                pass

        # Bazı Tk/Linux kurulumlarında iconbitmap etkisiz kalabilir; PNG yedeği kullanılır.
        if png_path.exists():
            try:
                self._app_icon_image = tk.PhotoImage(file=str(png_path))
                self.iconphoto(True, self._app_icon_image)
            except tk.TclError:
                pass

    def _baslangic_tam_ekran_yap(self) -> None:
        """Programı açılışta ekranı dolduracak şekilde başlatır."""
        try:
            # Windows'ta başlık çubuğu ve görev çubuğu korunarak büyütülmüş pencere açılır.
            self.state("zoomed")
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)
            except tk.TclError:
                pass

        self.update_idletasks()
        # Bazı Linux/Tk kurulumlarında zoomed komutu hata vermeden etkisiz kalabilir.
        # Bu durumda ekran boyutuna göre manuel büyütme yapılır.
        if self.state() == "normal":
            genislik = self.winfo_screenwidth()
            yukseklik = self.winfo_screenheight()
            self.geometry(f"{genislik}x{yukseklik}+0+0")

        self.after(180, self._xray_sahnesini_ciz)

    def _tam_ekran_degistir(self, event: tk.Event | None = None) -> None:
        """F11 ile gerçek tam ekran modunu aç/kapatır."""
        mevcut = self.attributes("-fullscreen")
        try:
            tam_ekranda = bool(int(mevcut))
        except (TypeError, ValueError):
            tam_ekranda = bool(mevcut)
        self.attributes("-fullscreen", not tam_ekranda)

    def _tam_ekrandan_cik(self, event: tk.Event | None = None) -> None:
        """Esc ile gerçek tam ekrandan çıkar."""
        try:
            self.attributes("-fullscreen", False)
        except tk.TclError:
            pass

    def _ana_frame_boyut_degisti(self, event: tk.Event) -> None:
        """Kaydırılabilir ana alanın sınırlarını günceller."""
        self.ana_canvas.configure(scrollregion=self.ana_canvas.bbox("all"))

    def _ana_canvas_boyut_degisti(self, event: tk.Event) -> None:
        """Dar pencere modunda sıkışmayı önleyen içerik genişliği ayarı."""
        if self._ana_window_id is None:
            return
        icerik_genisligi = max(event.width, self._minimum_icerik_genisligi)
        self.ana_canvas.itemconfigure(self._ana_window_id, width=icerik_genisligi)
        self.ana_canvas.configure(scrollregion=self.ana_canvas.bbox("all"))

    def _mousewheel_kaydir(self, event: tk.Event) -> None:
        """Ana içerik alanında fare tekerleği ile dikey kaydırma yapar."""
        # Listbox/Text/Treeview gibi kendi kaydırması olan widget'ların tekerlek
        # davranışına karışma; sadece boş ana alanlarda dış kaydırmayı kullan.
        if event.widget.winfo_toplevel() is not self:
            return
        if event.widget.winfo_class() in {"Listbox", "Text", "Treeview"}:
            return
        if sys.platform == "darwin":
            delta = -1 if event.delta > 0 else 1
        else:
            delta = int(-1 * (event.delta / 120))
        self.ana_canvas.yview_scroll(delta, "units")

    def _stil_ayarla(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#f4f6f8")
        style.configure("TLabelframe", background="#f4f6f8", borderwidth=1)
        style.configure("TLabelframe.Label", background="#f4f6f8", font=("Arial", 10, "bold"))
        style.configure("TLabel", background="#f4f6f8")
        style.configure("Header.TLabel", font=("Arial", 18, "bold"), foreground="#1f2937")
        style.configure("Sub.TLabel", font=("Arial", 10), foreground="#4b5563")
        style.configure("Status.TLabel", font=("Arial", 12, "bold"), background="#ffffff")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))

    def _arayuz_olustur(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ttk.Frame(self, padding=(14, 12, 14, 6))
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="Bagaj Güvenlik Simülatörü", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Queue + Stack + Linked List veri yapılarını X-ray dedektör animasyonu ile gösterir. F11: gerçek tam ekran, Esc: çıkış.",
            style="Sub.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Pencere küçültüldüğünde widget'lar birbirinin içine sıkışmasın diye
        # ana içerik kaydırılabilir canvas içine alınır. Ekran genişledikçe içerik
        # canvas genişliğine yayılır, daraldıkça yatay/dikey kaydırma devreye girer.
        scroll_container = ttk.Frame(self)
        scroll_container.grid(row=1, column=0, sticky="nsew")
        scroll_container.grid_columnconfigure(0, weight=1)
        scroll_container.grid_rowconfigure(0, weight=1)

        self.ana_canvas = tk.Canvas(scroll_container, bg="#f4f6f8", highlightthickness=0)
        self.ana_canvas.grid(row=0, column=0, sticky="nsew")
        dikey_scroll = AutoScrollbar(scroll_container, orient="vertical", command=self.ana_canvas.yview)
        dikey_scroll.grid(row=0, column=1, sticky="ns")
        yatay_scroll = AutoScrollbar(scroll_container, orient="horizontal", command=self.ana_canvas.xview)
        yatay_scroll.grid(row=1, column=0, sticky="ew")
        self.ana_canvas.configure(yscrollcommand=dikey_scroll.set, xscrollcommand=yatay_scroll.set)

        ana_frame = ttk.Frame(self.ana_canvas, padding=(10, 4, 10, 10))
        self._ana_window_id = self.ana_canvas.create_window((0, 0), window=ana_frame, anchor="nw")
        self.ana_frame = ana_frame
        ana_frame.bind("<Configure>", self._ana_frame_boyut_degisti)
        self.ana_canvas.bind("<Configure>", self._ana_canvas_boyut_degisti)
        self.ana_canvas.bind_all("<MouseWheel>", self._mousewheel_kaydir)

        # Tam ekranda panellerin orantısız büyümemesi, pencere modunda ise
        # kullanılabilir genişliklerin daha dengeli dağılması için min değerler azaltıldı.
        ana_frame.grid_columnconfigure(0, weight=1, minsize=250)
        ana_frame.grid_columnconfigure(1, weight=3, minsize=520)
        ana_frame.grid_columnconfigure(2, weight=1, minsize=250)
        ana_frame.grid_rowconfigure(1, weight=1)
        ana_frame.grid_rowconfigure(3, weight=1)

        # Üst sol: yolcu kuyruğu
        queue_frame = ttk.LabelFrame(ana_frame, text="Yolcu Kuyruğu (Queue)", padding=8)
        queue_frame.grid(row=0, column=0, rowspan=2, padx=6, pady=6, sticky="nsew")
        queue_frame.grid_rowconfigure(0, weight=1)
        queue_frame.grid_columnconfigure(0, weight=1)
        self.queue_panel = tk.Listbox(queue_frame, height=16, activestyle="none")
        self.queue_panel.grid(row=0, column=0, sticky="nsew")
        queue_scroll = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_panel.yview)
        queue_scroll.grid(row=0, column=1, sticky="ns")
        self.queue_panel.configure(yscrollcommand=queue_scroll.set)

        # Üst orta: X-ray animasyonu
        xray_frame = ttk.LabelFrame(ana_frame, text="X-ray Dedektör ve Konveyör Bant", padding=8)
        xray_frame.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        xray_frame.grid_columnconfigure(0, weight=1)
        xray_frame.grid_rowconfigure(0, weight=0)
        self.xray_canvas = tk.Canvas(
            xray_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#0b1220",
            highlightthickness=0,
        )
        self.xray_canvas.grid(row=0, column=0, sticky="ew")
        self.xray_canvas.bind("<Configure>", self._xray_canvas_boyut_degisti)

        durum_frame = ttk.Frame(xray_frame, style="Card.TFrame", padding=8)
        durum_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        durum_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(durum_frame, text="Sonuç:", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.durum_label = ttk.Label(durum_frame, text="Beklemede", style="Status.TLabel")
        self.durum_label.grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Label(durum_frame, text="Sıradaki:", style="Status.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.siradaki_label = ttk.Label(durum_frame, text="Henüz seçilmedi", style="Status.TLabel")
        self.siradaki_label.grid(row=1, column=1, sticky="w", padx=(6, 0), pady=(4, 0))

        # Üst sağ: kara liste
        kara_frame = ttk.LabelFrame(ana_frame, text="Kara Liste (Linked List)", padding=8)
        kara_frame.grid(row=0, column=2, rowspan=2, padx=6, pady=6, sticky="nsew")
        kara_frame.grid_rowconfigure(0, weight=1)
        kara_frame.grid_columnconfigure(0, weight=1)
        self.kara_liste_panel = tk.Listbox(kara_frame, height=16, activestyle="none")
        self.kara_liste_panel.grid(row=0, column=0, sticky="nsew")
        kara_scroll = ttk.Scrollbar(kara_frame, orient="vertical", command=self.kara_liste_panel.yview)
        kara_scroll.grid(row=0, column=1, sticky="ns")
        self.kara_liste_panel.configure(yscrollcommand=kara_scroll.set)

        # Butonlar
        buton_frame = ttk.Frame(ana_frame, padding=(0, 4, 0, 4))
        buton_frame.grid(row=2, column=0, columnspan=3, padx=6, pady=6, sticky="ew")
        for col in range(8):
            buton_frame.grid_columnconfigure(col, weight=1)

        self.btn_yolcu_ekle = ttk.Button(buton_frame, text="Rastgele Yolcu Ekle", command=self.rastgele_yolcu_ekle)
        self.btn_yolcu_ekle.grid(row=0, column=0, padx=4, sticky="ew")

        self.btn_demo_yukle = ttk.Button(buton_frame, text="Demo Veri Yükle", command=self.demo_veri_yukle)
        self.btn_demo_yukle.grid(row=0, column=1, padx=4, sticky="ew")

        self.btn_baslat = ttk.Button(buton_frame, text="Simülasyonu Başlat", command=self.simulasyonu_baslat, style="Accent.TButton")
        self.btn_baslat.grid(row=0, column=2, padx=4, sticky="ew")

        self.btn_sifirla = ttk.Button(buton_frame, text="Simülasyonu Sıfırla", command=self.simulasyonu_sifirla)
        self.btn_sifirla.grid(row=0, column=3, padx=4, sticky="ew")

        self.btn_rapor_goster = ttk.Button(buton_frame, text="Raporu Göster", command=self.rapor_penceresi_goster)
        self.btn_rapor_goster.grid(row=0, column=4, padx=4, sticky="ew")

        self.btn_rapor = ttk.Button(buton_frame, text="TXT Rapor Kaydet", command=self.rapor_olustur)
        self.btn_rapor.grid(row=0, column=5, padx=4, sticky="ew")

        self.btn_rapor_klasor = ttk.Button(buton_frame, text="Rapor Klasörünü Aç", command=self.rapor_klasorunu_ac)
        self.btn_rapor_klasor.grid(row=0, column=6, padx=4, sticky="ew")

        self.btn_cikis = ttk.Button(buton_frame, text="Çıkış", command=self.destroy)
        self.btn_cikis.grid(row=0, column=7, padx=4, sticky="ew")

        # Alt sol: stack listesi
        stack_frame = ttk.LabelFrame(ana_frame, text="Son Taranan Bagaj İçeriği (Stack)", padding=8)
        stack_frame.grid(row=3, column=0, padx=6, pady=6, sticky="nsew")
        stack_frame.grid_columnconfigure(0, weight=1)
        stack_frame.grid_rowconfigure(0, weight=1)
        self.stack_panel = tk.Listbox(stack_frame, height=13, activestyle="none")
        self.stack_panel.grid(row=0, column=0, sticky="nsew")
        stack_scroll = ttk.Scrollbar(stack_frame, orient="vertical", command=self.stack_panel.yview)
        stack_scroll.grid(row=0, column=1, sticky="ns")
        self.stack_panel.configure(yscrollcommand=stack_scroll.set)

        # Alt orta: loglar
        log_frame = ttk.LabelFrame(ana_frame, text="Olay Logları", padding=8)
        log_frame.grid(row=3, column=1, padx=6, pady=6, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.log_panel = tk.Listbox(log_frame, height=13, activestyle="none")
        self.log_panel.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_panel.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_panel.configure(yscrollcommand=log_scroll.set)

        # Alt sağ: sayaç kartı
        sayac_frame = ttk.LabelFrame(ana_frame, text="Canlı Sayaçlar", padding=10)
        sayac_frame.grid(row=3, column=2, padx=6, pady=6, sticky="nsew")
        sayac_frame.grid_columnconfigure(0, weight=1)
        self.sayac_label = tk.Label(
            sayac_frame,
            text="",
            justify="left",
            anchor="nw",
            bg="#ffffff",
            fg="#111827",
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.sayac_label.grid(row=0, column=0, sticky="nsew")

        self.aciklama_label = ttk.Label(
            ana_frame,
            text="Renkler: kırmızı = yasaklı eşya/alarm, turuncu = kara liste, yeşil = temiz geçiş. Bagaj X-ray tünelinden geçerken içindeki eşyalar görsel olarak gösterilir.",
            style="Sub.TLabel",
        )
        self.aciklama_label.grid(row=4, column=0, columnspan=3, padx=8, pady=(0, 4), sticky="ew")

    # ------------------------------------------------------------------
    # X-ray Canvas çizimleri
    # ------------------------------------------------------------------
    def _xray_canvas_boyut_degisti(self, event: tk.Event) -> None:
        """Canvas genişliği değişince X-ray sahnesini yeniden çizer.

        Önceki sürümde çizim koordinatları sabit kaldığı için pencere tam ekrana
        alındığında dedektör görüntüsü sol tarafta küçük kalıyordu. Bu yöntem,
        sahneyi mevcut canvas genişliğine göre yeniden ölçekler/ortalar.
        """
        if event.width < 300:
            return
        if self._canvas_resize_job:
            self.after_cancel(self._canvas_resize_job)
        self._canvas_resize_job = self.after(80, self._xray_sahnesini_ciz)

    def _xray_sahnesini_ciz(self) -> None:
        self.xray_canvas.delete("all")
        mevcut_genislik = self.xray_canvas.winfo_width()
        w = max(520, mevcut_genislik if mevcut_genislik > 1 else self.base_canvas_width)
        h = self.canvas_height
        self.canvas_width = w
        self.xray_canvas.configure(height=h)

        # Arka plan
        self.xray_canvas.create_rectangle(0, 0, w, h, fill="#0b1220", outline="")
        self.xray_canvas.create_text(18, 18, text="X-RAY BAGAJ TARAMA SİSTEMİ", anchor="w", fill="#e5e7eb", font=("Arial", 13, "bold"))
        self.xray_canvas.create_text(w - 18, 18, text="CANLI SİMÜLASYON", anchor="e", fill="#38bdf8", font=("Arial", 10, "bold"))

        # Konveyör bant
        belt_y1, belt_y2 = 172, 212
        self.xray_canvas.create_rectangle(20, belt_y1, w - 20, belt_y2, fill="#334155", outline="#64748b", width=2)
        for x in range(35, int(w) - 30, 38):
            self.xray_canvas.create_oval(x, 181, x + 20, 201, fill="#111827", outline="#94a3b8")
            self.xray_canvas.create_line(x + 10, 181, x + 10, 201, fill="#475569")

        # Dedektör tüneli: canvas genişliğine göre merkeze alınır.
        merkez_x = w / 2
        dedektor_genislik = 190
        self.detector_x1 = int(merkez_x - dedektor_genislik / 2)
        self.detector_x2 = int(merkez_x + dedektor_genislik / 2)
        self.detector_y1, self.detector_y2 = 72, 222

        self.xray_canvas.create_rectangle(self.detector_x1 - 18, self.detector_y1 - 10, self.detector_x2 + 18, self.detector_y2, fill="#1f2937", outline="#93c5fd", width=3)
        self.xray_canvas.create_rectangle(self.detector_x1, self.detector_y1, self.detector_x2, self.detector_y2 - 18, fill="#0f172a", outline="#60a5fa", width=2)
        self.xray_canvas.create_rectangle(self.detector_x1 + 14, self.detector_y1 + 18, self.detector_x2 - 14, self.detector_y2 - 35, fill="#082f49", outline="#38bdf8", width=2)
        self.xray_canvas.create_text((self.detector_x1 + self.detector_x2) / 2, self.detector_y1 + 10, text="DEDEKTÖR", fill="#bfdbfe", font=("Arial", 10, "bold"))

        # Giriş/çıkış işaretleri de genişliğe göre konumlanır.
        self.entry_text_x = max(90, self.detector_x1 - 230)
        self.result_text_x = min(w - 90, self.detector_x2 + 230)
        self.xray_canvas.create_text(self.entry_text_x, 65, text="GİRİŞ", fill="#cbd5e1", font=("Arial", 10, "bold"))
        self.xray_canvas.create_text(self.result_text_x, 65, text="SONUÇ", fill="#cbd5e1", font=("Arial", 10, "bold"))
        self.xray_canvas.create_line(self.entry_text_x + 35, 92, self.detector_x1 - 24, 92, fill="#38bdf8", width=3, arrow=tk.LAST)
        self.xray_canvas.create_line(self.detector_x2 + 24, 92, self.result_text_x - 35, 92, fill="#38bdf8", width=3, arrow=tk.LAST)

        self._dinamik_canvas_items.clear()
        self._bagaj_items.clear()
        self._bekleme_ekranini_goster()

    def _bekleme_ekranini_goster(self) -> None:
        self._dinamikleri_temizle()
        self._dinamik_canvas_items.append(
            self.xray_canvas.create_text(
                self.canvas_width / 2,
                135,
                text="Simülasyon bekleniyor",
                fill="#94a3b8",
                font=("Arial", 14, "bold"),
            )
        )

    def _dinamikleri_temizle(self) -> None:
        for item in self._dinamik_canvas_items + self._bagaj_items:
            self.xray_canvas.delete(item)
        self._dinamik_canvas_items.clear()
        self._bagaj_items.clear()

    def _bagaj_ciz(self, x: int, y: int, result: ScanResult) -> None:
        self._bagaj_items.clear()
        outline = "#ef4444" if result.alarm_var else "#22c55e"
        fill = "#78350f" if result.alarm_var else "#1e3a8a"

        # Valiz gövdesi ve tutacak
        self._bagaj_items.append(self.xray_canvas.create_rectangle(x, y, x + 84, y + 48, fill=fill, outline=outline, width=3))
        self._bagaj_items.append(self.xray_canvas.create_rectangle(x + 27, y - 12, x + 57, y + 2, fill="#0f172a", outline=outline, width=2))
        self._bagaj_items.append(self.xray_canvas.create_line(x + 15, y + 11, x + 69, y + 11, fill="#93c5fd", width=2))
        self._bagaj_items.append(self.xray_canvas.create_oval(x + 14, y + 43, x + 25, y + 54, fill="#111827", outline="#e5e7eb"))
        self._bagaj_items.append(self.xray_canvas.create_oval(x + 60, y + 43, x + 71, y + 54, fill="#111827", outline="#e5e7eb"))

        etiket = result.yolcu.unique_id
        self._bagaj_items.append(self.xray_canvas.create_text(x + 42, y + 29, text=etiket, fill="#f8fafc", font=("Arial", 8, "bold")))

    def _xray_icerik_goster(self, result: ScanResult) -> None:
        # Dedektör ekranı içindeki eşya görüntüleri
        x0, y0 = self.detector_x1 + 26, self.detector_y1 + 42
        for idx, esya in enumerate(result.yolcu.bagaj[:8]):
            col = idx % 2
            row = idx // 2
            x = x0 + col * 70
            y = y0 + row * 24
            yasakli = esya in YASAKLI_ESYALAR
            renk = "#f87171" if yasakli else "#67e8f9"
            kutu = self.xray_canvas.create_rectangle(x, y, x + 56, y + 17, fill="#0f172a", outline=renk, width=2)
            yazi = self.xray_canvas.create_text(x + 28, y + 9, text=esya[:12], fill=renk, font=("Arial", 7, "bold"))
            self._dinamik_canvas_items.extend([kutu, yazi])

        # Tarama ışını
        for i in range(4):
            beam = self.xray_canvas.create_line(
                self.detector_x1 + 18 + i * 32,
                self.detector_y1 + 36,
                self.detector_x1 + 56 + i * 32,
                self.detector_y2 - 52,
                fill="#22d3ee",
                width=2,
            )
            self._dinamik_canvas_items.append(beam)

    def _sonuc_rozetini_goster(self, result: ScanResult) -> None:
        if result.bulunan_yasakli_esyalar:
            metin = "ALARM"
            detay = ", ".join(result.bulunan_yasakli_esyalar)
            renk = "#ef4444"
            dolgu = "#450a0a"
        elif result.onceki_kara_liste:
            metin = "KARA LİSTE"
            detay = "Detaylı kontrol"
            renk = "#f97316"
            dolgu = "#431407"
        else:
            metin = "TEMİZ"
            detay = "Geçiş onaylandı"
            renk = "#22c55e"
            dolgu = "#052e16"

        rozet_w = 150
        ideal_x1 = self.detector_x2 + 70
        x1 = int(min(self.canvas_width - rozet_w - 25, max(25, ideal_x1)))
        y1, x2, y2 = 108, x1 + rozet_w, 165
        self._dinamik_canvas_items.append(self.xray_canvas.create_rectangle(x1, y1, x2, y2, fill=dolgu, outline=renk, width=3))
        self._dinamik_canvas_items.append(self.xray_canvas.create_text((x1 + x2) / 2, y1 + 20, text=metin, fill=renk, font=("Arial", 14, "bold")))
        self._dinamik_canvas_items.append(self.xray_canvas.create_text((x1 + x2) / 2, y1 + 42, text=detay[:22], fill="#f8fafc", font=("Arial", 8, "bold")))

    def _xray_animasyon_baslat(self, result: ScanResult) -> None:
        self._aktif_result = result
        self._animasyon_step = 0
        self._dinamikleri_temizle()
        self.siradaki_label.config(text=f"{result.yolcu.gorunen_ad} | {result.yolcu.unique_id}")
        self.durum_label.config(text="Bagaj dedektöre ilerliyor...")
        self._xray_animasyon_adimi()

    def _xray_animasyon_adimi(self) -> None:
        if not self._aktif_result:
            return

        result = self._aktif_result
        for item in self._bagaj_items:
            self.xray_canvas.delete(item)
        self._bagaj_items.clear()

        start_x = max(35, self.detector_x1 - 250)
        end_x = min(self.canvas_width - 125, self.detector_x2 + 140)
        y = 124
        oran = self._animasyon_step / self._animasyon_max_step
        x = int(start_x + (end_x - start_x) * oran)
        self._bagaj_ciz(x, y, result)

        # Tünele girince içerik ve tarama çizgileri görünür.
        if self.detector_x1 - 20 <= x + 42 <= self.detector_x2 + 20:
            self.durum_label.config(text="X-ray taraması yapılıyor...")
            # Işınlar ve içerik bir kez çizilip sonra yenilenir.
            for item in self._dinamik_canvas_items:
                self.xray_canvas.delete(item)
            self._dinamik_canvas_items.clear()
            self._xray_icerik_goster(result)

        if self._animasyon_step < self._animasyon_max_step:
            self._animasyon_step += 1
            self.after(22, self._xray_animasyon_adimi)
            return

        self._sonuc_rozetini_goster(result)
        if result.bulunan_yasakli_esyalar:
            self.durum_label.config(text=f"ALARM: {', '.join(result.bulunan_yasakli_esyalar)}")
        elif result.onceki_kara_liste:
            self.durum_label.config(text="KARA LİSTE: Yolcu detaylı kontrole sevk edildi")
        else:
            self.durum_label.config(text="TEMİZ: Bagaj geçişe uygun")

        # Ses artık her eşya için değil, her yolcu sonucu için yalnızca 1 kez çalıyor.
        # Normal geçiş ayrı; yasaklı eşya / kara liste gibi tüm kötü sonuçlar aynı alarm sesini kullanıyor.
        sonuc_sesi_cal(kotu_sonuc=result.alarm_var)
        self.after(420, self._animasyon_bitti)

    def _animasyon_bitti(self) -> None:
        if not self._aktif_result:
            return
        result = self._aktif_result
        self._aktif_result = None
        self._stack_panel_guncelle(result.yolcu, result)
        self._kara_liste_panel_guncelle()
        self._sayac_panel_guncelle()
        self._loglari_guncelle()
        self.after(160, self._siradaki_yolcuyu_isle)

    # ------------------------------------------------------------------
    # Panel güncellemeleri ve buton işlemleri
    # ------------------------------------------------------------------
    def _log_yaz(self, mesaj: str) -> None:
        self.simulator.log_yaz(mesaj)
        self._loglari_guncelle()

    def _loglari_guncelle(self) -> None:
        self.log_panel.delete(0, tk.END)
        for log in self.simulator.loglar[-300:]:
            self.log_panel.insert(tk.END, log)
        self.log_panel.yview(tk.END)

    def _queue_panel_guncelle(self) -> None:
        self.queue_panel.delete(0, tk.END)
        for yolcu in self.simulator.passenger_queue:
            self.queue_panel.insert(tk.END, str(yolcu))

    def _stack_panel_guncelle(self, yolcu: Passenger | None = None, result: ScanResult | None = None) -> None:
        self.stack_panel.delete(0, tk.END)
        if not yolcu:
            return

        self.stack_panel.insert(tk.END, f"{yolcu.gorunen_ad} | {yolcu.unique_id}")
        self.stack_panel.itemconfig(0, fg="#111827")
        self.stack_panel.insert(tk.END, "--- Bagaj eşyaları ---")
        self.stack_panel.itemconfig(1, fg="#2563eb")

        for idx, esya in enumerate(yolcu.bagaj, start=2):
            self.stack_panel.insert(tk.END, esya)
            if esya in YASAKLI_ESYALAR:
                self.stack_panel.itemconfig(idx, fg="red")
            else:
                self.stack_panel.itemconfig(idx, fg="green")

        if result and result.onceki_kara_liste:
            self.stack_panel.insert(tk.END, "--- Yolcu kara listede kayıtlı ---")
            self.stack_panel.itemconfig(tk.END, fg="orange")

    def _kara_liste_panel_guncelle(self) -> None:
        self.kara_liste_panel.delete(0, tk.END)
        for yolcu_id in self.simulator.kara_liste.listele():
            self.kara_liste_panel.insert(tk.END, yolcu_id)

    def _sayac_panel_guncelle(self) -> None:
        stats = self.simulator.istatistikler()
        self.sayac_label.config(
            text=(
                f"İşlenen Yolcu       : {stats['islenen_yolcu_sayisi']}\n"
                f"Kuyrukta Bekleyen   : {stats['kuyrukta_bekleyen']}\n"
                f"Alarm/Yasaklı Eşya  : {stats['alarm_sayisi']}\n"
                f"Engellenen Yolcu    : {stats['engellenen_yolcu_sayisi']}\n"
                f"Temiz Geçen         : {stats['temiz_gecen_sayisi']}\n"
                f"Kara Liste Kaydı    : {stats['kara_liste_sayisi']}\n"
                f"Toplam Bagaj/Eşya   : {stats['toplam_bagaj_sayisi']}\n\n"
                f"Temiz Geçiş Oranı   : %{stats['temiz_gecis_orani']:.2f}\n"
                f"Alarmlı Yolcu Oranı : %{stats['alarmli_yolcu_orani']:.2f}"
            )
        )

    def rastgele_yolcu_ekle(self) -> None:
        yolcu = self.simulator.rastgele_yolcu_ekle()
        self.queue_panel.insert(tk.END, str(yolcu))
        self._loglari_guncelle()
        self._sayac_panel_guncelle()
        self.durum_label.config(text="Rastgele yolcu kuyruğa eklendi")

    def demo_veri_yukle(self) -> None:
        self.simulator.demo_veri_yukle(toplam_yolcu=30)
        self._queue_panel_guncelle()
        self._kara_liste_panel_guncelle()
        self._sayac_panel_guncelle()
        self._loglari_guncelle()
        self.durum_label.config(text="Demo veriler yüklendi")
        messagebox.showinfo("Bilgi", "Demo veriler yüklendi. İçinde temiz, tehlikeli ve kara listedeki yolcular vardır.")

    def simulasyonu_baslat(self) -> None:
        if self.simulasyon_calisiyor:
            return
        if not self.simulator.passenger_queue:
            messagebox.showwarning("Uyarı", "Kuyrukta yolcu yok. Önce demo veri yükleyin veya rastgele yolcu ekleyin.")
            return

        self.simulasyon_calisiyor = True
        self._buton_durumlarini_ayarla(tk.DISABLED)
        self.btn_baslat.config(state=tk.DISABLED)
        self._siradaki_yolcuyu_isle()

    def _siradaki_yolcuyu_isle(self) -> None:
        result = self.simulator.siradaki_yolcuyu_tara()
        if result:
            self._queue_panel_guncelle()
            self._xray_animasyon_baslat(result)
            return

        self.simulasyon_calisiyor = False
        self._buton_durumlarini_ayarla(tk.NORMAL)
        self.btn_baslat.config(state=tk.NORMAL)
        self._loglari_guncelle()
        self._sayac_panel_guncelle()
        self.durum_label.config(text="Simülasyon tamamlandı")
        self.siradaki_label.config(text="Kuyrukta yolcu kalmadı")
        messagebox.showinfo("Tamamlandı", "Simülasyon tamamlandı. Raporu uygulama içinde görüntüleyebilir veya TXT olarak kaydedebilirsiniz.")

    def _buton_durumlarini_ayarla(self, durum: str) -> None:
        # Simülasyon akarken çift başlatma veya veri ekleme kaynaklı karışıklığı önler.
        self.btn_yolcu_ekle.config(state=durum)
        self.btn_demo_yukle.config(state=durum)
        self.btn_sifirla.config(state=durum)
        self.btn_rapor.config(state=durum)
        self.btn_rapor_goster.config(state=durum)

    def simulasyonu_sifirla(self) -> None:
        if self.simulasyon_calisiyor:
            messagebox.showwarning("Uyarı", "Simülasyon çalışırken sıfırlama yapılamaz.")
            return
        self.simulator.reset()
        self._queue_panel_guncelle()
        self._stack_panel_guncelle()
        self._kara_liste_panel_guncelle()
        self._sayac_panel_guncelle()
        self._loglari_guncelle()
        self._xray_sahnesini_ciz()
        self.durum_label.config(text="Sistem sıfırlandı")
        self.siradaki_label.config(text="Henüz seçilmedi")

    # ------------------------------------------------------------------
    # Rapor işlemleri
    # ------------------------------------------------------------------
    def rapor_penceresi_goster(self) -> None:
        stats = self.simulator.istatistikler()
        pencere = tk.Toplevel(self)
        pencere.title("Gün Sonu Raporu")
        pencere.minsize(850, 620)
        pencere.configure(bg="#f4f6f8")
        pencere.transient(self)

        kapsayici = ttk.Frame(pencere, padding=14)
        kapsayici.pack(fill="both", expand=True)
        kapsayici.grid_columnconfigure(0, weight=1)
        kapsayici.grid_rowconfigure(2, weight=1)

        ttk.Label(kapsayici, text="Gün Sonu Güvenlik Raporu", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(kapsayici, text="Uygulama içi özet ekranı — TXT dosyası açmadan raporu görüntüler.", style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 10))

        kartlar = ttk.Frame(kapsayici)
        kartlar.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        for col in range(4):
            kartlar.grid_columnconfigure(col, weight=1)
        self._rapor_karti(kartlar, 0, "İşlenen Yolcu", str(stats["islenen_yolcu_sayisi"]), "#1d4ed8")
        self._rapor_karti(kartlar, 1, "Alarm/Yasaklı", str(stats["alarm_sayisi"]), "#dc2626")
        self._rapor_karti(kartlar, 2, "Temiz Geçen", str(stats["temiz_gecen_sayisi"]), "#16a34a")
        self._rapor_karti(kartlar, 3, "Kara Liste", str(stats["kara_liste_sayisi"]), "#f97316")

        detay = ttk.Frame(kapsayici)
        detay.grid(row=3, column=0, sticky="nsew")
        detay.grid_columnconfigure(0, weight=1)
        detay.grid_columnconfigure(1, weight=1)
        detay.grid_rowconfigure(0, weight=1)

        esya_frame = ttk.LabelFrame(detay, text="Yakalanan Yasaklı Eşyalar", padding=8)
        esya_frame.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        esya_frame.grid_columnconfigure(0, weight=1)
        esya_frame.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(esya_frame, columns=("esya", "adet"), show="headings", height=8)
        tree.heading("esya", text="Yasaklı Eşya")
        tree.heading("adet", text="Adet")
        tree.column("esya", width=220)
        tree.column("adet", width=70, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        if self.simulator.yakalanan_esya_sayaci:
            for esya, adet in self.simulator.yakalanan_esya_sayaci.most_common():
                tree.insert("", "end", values=(esya, adet))
        else:
            tree.insert("", "end", values=("Yok", 0))

        metin_frame = ttk.LabelFrame(detay, text="Rapor Metni", padding=8)
        metin_frame.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        metin_frame.grid_columnconfigure(0, weight=1)
        metin_frame.grid_rowconfigure(0, weight=1)
        rapor_metin = tk.Text(metin_frame, wrap="word", height=20, bg="#ffffff", font=("Consolas", 9))
        rapor_metin.insert("1.0", self.simulator.rapor_olustur())
        rapor_metin.configure(state="disabled")
        rapor_metin.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(metin_frame, orient="vertical", command=rapor_metin.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        rapor_metin.configure(yscrollcommand=scroll.set)

        alt = ttk.Frame(kapsayici)
        alt.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        alt.grid_columnconfigure(0, weight=1)
        ttk.Button(alt, text="TXT Olarak Kaydet", command=self.rapor_olustur).grid(row=0, column=1, padx=4)
        ttk.Button(alt, text="Kapat", command=pencere.destroy).grid(row=0, column=2, padx=4)

    def _rapor_karti(self, parent: ttk.Frame, col: int, baslik: str, deger: str, renk: str) -> None:
        kart = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#d1d5db")
        kart.grid(row=0, column=col, padx=5, sticky="ew")
        tk.Label(kart, text=baslik, bg="#ffffff", fg="#4b5563", font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        tk.Label(kart, text=deger, bg="#ffffff", fg=renk, font=("Arial", 20, "bold")).pack(anchor="w", padx=10, pady=(0, 8))

    def rapor_olustur(self) -> None:
        rapor_yolu = self.simulator.rapor_kaydet(self.reports_dir)
        self._loglari_guncelle()
        messagebox.showinfo("Rapor Oluşturuldu", f"Rapor kaydedildi:\n{rapor_yolu}")

    def rapor_klasorunu_ac(self) -> None:
        self.reports_dir.mkdir(exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(self.reports_dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.reports_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.reports_dir)])
        except Exception as exc:
            messagebox.showerror("Hata", f"Rapor klasörü açılamadı:\n{exc}")
