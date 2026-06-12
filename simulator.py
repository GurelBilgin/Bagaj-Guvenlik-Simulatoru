"""Bagaj güvenlik simülasyonunun temel işlem mantığı."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from constants import BASLANGIC_KARA_LISTE, YASAKLI_ESYALAR
from linked_list import LinkedList
from passenger import Passenger


@dataclass
class ScanResult:
    yolcu: Passenger
    onceki_kara_liste: bool
    bulunan_yasakli_esyalar: list[str]
    kara_listeye_yeni_eklendi: bool
    temiz_gecis: bool

    @property
    def alarm_var(self) -> bool:
        return bool(self.bulunan_yasakli_esyalar) or self.onceki_kara_liste


class BaggageSecuritySimulator:
    """Queue, stack ve linked list kullanan bagaj güvenlik simülatörü."""

    def __init__(self) -> None:
        self.passenger_queue: deque[Passenger] = deque()
        self.baggage_stack: list[str] = []
        self.kara_liste = LinkedList()
        self.loglar: list[str] = []
        self.reset_sayaclar()
        self.baslangic_kara_liste_yukle()

    def reset_sayaclar(self) -> None:
        self.temiz_gecenler: list[Passenger] = []
        self.engellenen_yolcular: list[Passenger] = []
        self.kara_listede_yakalananlar: list[Passenger] = []
        self.kara_listeye_yeni_eklenenler: list[Passenger] = []
        self.tehlikeli_esya_yakalanan_yolcular: list[Passenger] = []
        self.yakalanan_esya_sayaci: Counter[str] = Counter()
        self.toplam_bagaj_sayisi = 0
        self.islenen_yolcu_sayisi = 0
        self.alarm_sayisi = 0

    def reset(self) -> None:
        self.passenger_queue.clear()
        self.baggage_stack.clear()
        self.kara_liste.temizle()
        self.loglar.clear()
        self.reset_sayaclar()
        self.baslangic_kara_liste_yukle()
        self.log_yaz("Sistem sıfırlandı. Başlangıç kara listesi yeniden yüklendi.")

    def baslangic_kara_liste_yukle(self) -> None:
        for yolcu_id in BASLANGIC_KARA_LISTE:
            self.kara_liste.ekle(yolcu_id)

    def log_yaz(self, mesaj: str) -> None:
        saat = datetime.now().strftime("%H:%M:%S")
        self.loglar.append(f"[{saat}] {mesaj}")

    def yolcu_ekle(self, yolcu: Passenger) -> None:
        self.passenger_queue.append(yolcu)
        self.log_yaz(f"{yolcu.gorunen_ad} kuyruğa eklendi. ID: {yolcu.unique_id}")

    def rastgele_yolcu_ekle(self) -> Passenger:
        yolcu = Passenger.rastgele_olustur()
        self.yolcu_ekle(yolcu)
        return yolcu

    def demo_veri_yukle(self, toplam_yolcu: int = 30) -> None:
        demo_yolcular = Passenger.demo_yolcular()
        for yolcu in demo_yolcular:
            self.yolcu_ekle(yolcu)

        kalan = max(0, toplam_yolcu - len(demo_yolcular))
        for _ in range(kalan):
            self.rastgele_yolcu_ekle()

        self.log_yaz(f"Demo + rastgele toplam {len(demo_yolcular) + kalan} yolcu yüklendi.")

    def siradaki_yolcuyu_tara(self) -> ScanResult | None:
        """Kuyruktaki ilk yolcuyu çıkarır ve bagajını stack mantığıyla tarar."""
        if not self.passenger_queue:
            self.log_yaz("Kuyrukta işlenecek yolcu kalmadı.")
            return None

        yolcu = self.passenger_queue.popleft()
        self.islenen_yolcu_sayisi += 1
        self.log_yaz(f"{yolcu.gorunen_ad} kontrol ediliyor. ID: {yolcu.unique_id}")

        onceki_kara_liste = self.kara_liste.kontrol(yolcu.unique_id)
        if onceki_kara_liste:
            self.kara_listede_yakalananlar.append(yolcu)
            self.log_yaz(f"UYARI: {yolcu.gorunen_ad} önceden kara listede kayıtlı!")

        self.baggage_stack.clear()
        for esya in yolcu.bagaj:
            self.baggage_stack.append(esya)
            self.toplam_bagaj_sayisi += 1

        bulunan_yasakli_esyalar: list[str] = []
        self.log_yaz("Bagaj stack yapısına alındı. Tarama LIFO mantığıyla başlatıldı.")

        while self.baggage_stack:
            esya = self.baggage_stack.pop()
            if esya in YASAKLI_ESYALAR:
                bulunan_yasakli_esyalar.append(esya)
                self.yakalanan_esya_sayaci[esya] += 1
                self.alarm_sayisi += 1
                self.log_yaz(f"ALARM: {esya} bulundu!")

        kara_listeye_yeni_eklendi = False
        if bulunan_yasakli_esyalar:
            self.tehlikeli_esya_yakalanan_yolcular.append(yolcu)
            self.engellenen_yolcular.append(yolcu)
            if self.kara_liste.ekle(yolcu.unique_id):
                kara_listeye_yeni_eklendi = True
                self.kara_listeye_yeni_eklenenler.append(yolcu)
                self.log_yaz(f"{yolcu.gorunen_ad} kara listeye yeni eklendi. ID: {yolcu.unique_id}")
            self.log_yaz(f"{yolcu.gorunen_ad} geçişi engellendi. Bulunan: {', '.join(bulunan_yasakli_esyalar)}")
        elif onceki_kara_liste:
            self.engellenen_yolcular.append(yolcu)
            self.log_yaz(f"{yolcu.gorunen_ad} kara liste nedeniyle detaylı kontrole sevk edildi.")
        else:
            self.temiz_gecenler.append(yolcu)
            self.log_yaz(f"{yolcu.gorunen_ad} güvenli olarak geçiş yaptı.")

        return ScanResult(
            yolcu=yolcu,
            onceki_kara_liste=onceki_kara_liste,
            bulunan_yasakli_esyalar=bulunan_yasakli_esyalar,
            kara_listeye_yeni_eklendi=kara_listeye_yeni_eklendi,
            temiz_gecis=not bulunan_yasakli_esyalar and not onceki_kara_liste,
        )

    def istatistikler(self) -> dict[str, float | int]:
        if self.islenen_yolcu_sayisi == 0:
            temiz_oran = 0.0
            alarm_oran = 0.0
        else:
            temiz_oran = len(self.temiz_gecenler) / self.islenen_yolcu_sayisi * 100
            alarmli_yolcu_sayisi = len(self.engellenen_yolcular)
            alarm_oran = alarmli_yolcu_sayisi / self.islenen_yolcu_sayisi * 100

        return {
            "islenen_yolcu_sayisi": self.islenen_yolcu_sayisi,
            "kuyrukta_bekleyen": len(self.passenger_queue),
            "toplam_bagaj_sayisi": self.toplam_bagaj_sayisi,
            "alarm_sayisi": self.alarm_sayisi,
            "engellenen_yolcu_sayisi": len(self.engellenen_yolcular),
            "temiz_gecen_sayisi": len(self.temiz_gecenler),
            "kara_liste_sayisi": len(self.kara_liste),
            "temiz_gecis_orani": temiz_oran,
            "alarmli_yolcu_orani": alarm_oran,
        }

    def rapor_olustur(self) -> str:
        tarih_saat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats = self.istatistikler()

        en_sik_esya = "Yok"
        if self.yakalanan_esya_sayaci:
            esya, adet = self.yakalanan_esya_sayaci.most_common(1)[0]
            en_sik_esya = f"{esya} ({adet} adet)"

        def yolcu_listele(yolcular: list[Passenger]) -> str:
            if not yolcular:
                return "Yok"
            return ", ".join(f"{y.gorunen_ad} [{y.unique_id}]" for y in yolcular)

        esya_detay = "Yok"
        if self.yakalanan_esya_sayaci:
            esya_detay = ", ".join(
                f"{esya}: {adet}" for esya, adet in self.yakalanan_esya_sayaci.most_common()
            )

        rapor_satirlari = [
            "----- BAGAJ GÜVENLİK SİMÜLATÖRÜ GÜN SONU RAPORU -----",
            f"Tarih: {tarih_saat}",
            "",
            "GENEL ÖZET",
            f"Toplam işlenen yolcu sayısı: {stats['islenen_yolcu_sayisi']}",
            f"Kuyrukta bekleyen yolcu sayısı: {stats['kuyrukta_bekleyen']}",
            f"Stack'e alınan toplam bagaj/eşya sayısı: {stats['toplam_bagaj_sayisi']}",
            f"Alarm sayısı / yakalanan yasaklı eşya adedi: {stats['alarm_sayisi']}",
            f"Tehlikeli eşya veya kara liste nedeniyle engellenen yolcu: {stats['engellenen_yolcu_sayisi']}",
            f"Temiz geçiş yapan yolcu sayısı: {stats['temiz_gecen_sayisi']}",
            f"Temiz geçiş oranı: %{stats['temiz_gecis_orani']:.2f}",
            f"Alarm verilen yolcu oranı: %{stats['alarmli_yolcu_orani']:.2f}",
            "",
            "YASAKLI EŞYA DETAYI",
            f"Bulunan yasaklı eşyalar: {esya_detay}",
            f"En sık yakalanan yasaklı eşya: {en_sik_esya}",
            "",
            "KARA LİSTE DETAYI",
            f"Mevcut kara liste ID'leri: {', '.join(self.kara_liste.listele()) or 'Yok'}",
            f"Önceden kara listede yakalananlar: {yolcu_listele(self.kara_listede_yakalananlar)}",
            f"Kara listeye yeni eklenenler: {yolcu_listele(self.kara_listeye_yeni_eklenenler)}",
            "",
            "YOLCU DETAYI",
            f"Temiz geçenler: {yolcu_listele(self.temiz_gecenler)}",
            f"Engellenenler: {yolcu_listele(self.engellenen_yolcular)}",
            "",
            "KULLANILAN VERİ YAPILARI",
            "Queue / deque: Yolcu kuyruğu için kullanıldı.",
            "Stack / list: Bagaj eşyalarını LIFO mantığıyla taramak için kullanıldı.",
            "Linked List: Kara listedeki yolcu ID'lerini tutmak için kullanıldı.",
            "---------------------------------------------------------",
        ]
        return "\n".join(rapor_satirlari)

    def rapor_kaydet(self, reports_dir: str | Path = "reports") -> Path:
        reports_path = Path(reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)

        zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
        rapor_yolu = reports_path / f"gun_sonu_raporu_{zaman}.txt"
        rapor_yolu.write_text(self.rapor_olustur(), encoding="utf-8")

        # Son rapora hızlı erişim için sabit isimli kopya da oluşturulur.
        (reports_path / "son_gun_sonu_raporu.txt").write_text(self.rapor_olustur(), encoding="utf-8")
        self.log_yaz(f"Rapor kaydedildi: {rapor_yolu}")
        return rapor_yolu
