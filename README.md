# Bagaj Güvenlik Simülatörü

Bu proje, bagaj güvenlik kontrol sürecini veri yapıları kullanarak simüle eden bir Python/Tkinter uygulamasıdır. Uygulamada yolcular sırayla güvenlik kontrolüne alınır, bagaj içerikleri stack mantığıyla taranır ve riskli yolcular kara listeye bağlı liste yapısıyla eklenir.

## Kullanılan veri yapıları

- **Queue / deque:** Yolcular sırayla güvenlik kontrolüne alınır.
- **Stack / list:** Bagajdaki eşyalar LIFO mantığıyla taranır.
- **Linked List:** Kara listedeki yolcu ID'leri tutulur.

## Özellikler

- Rastgele yolcu üretme
- Demo veri yükleme
- Temiz, tehlikeli ve kara listedeki yolcuları simüle etme
- X-ray dedektör ve konveyör bant animasyonu
- Bagaj dedektörden geçerken eşya içeriğini görsel olarak gösterme
- Yasaklı eşyaları kırmızı, temiz eşyaları yeşil/mavi tonlarında gösterme
- Temiz geçişte normal ses, yasaklı eşya/kara listede alarm sesi çalma
- Yasaklı eşya veya kara liste durumunda alarm sonucu üretme
- Kara listeye otomatik ekleme
- Önceden kara listede olan yolcuları yakalama
- Uygulama içinde estetik gün sonu raporu görüntüleme
- İstenirse TXT rapor kaydetme
- Temiz geçiş oranı ve alarm oranı hesaplama
- Programı açılışta otomatik büyütülmüş/tam ekran pencere olarak başlatma
- Pencere moduna alınca arayüzü kaydırılabilir ve responsive düzende koruma
- Tam ekran kullanımda X-ray sahnesini mevcut pencere genişliğine göre ortalama
- Özel pencere/EXE ikonu desteği

## Yasaklı eşyalar

Yasaklı eşyalar `constants.py` dosyasında tek merkezden yönetilir:

- bıçak
- silah
- patlayıcı
- aerosol
- yanıcı madde

## Çalıştırma

Python 3 yüklü olmalıdır. Tkinter çoğu Python kurulumuyla birlikte gelir.

```bash
python main.py
```

## Kullanım

Program açılışta ekranı dolduracak şekilde başlar. Pencere moduna aldığınızda arayüz mümkün olduğu kadar yeniden ölçeklenir; pencere çok daraltılırsa panellerin birbirine girmemesi için yatay/dikey kaydırma çubukları devreye girer. F11 gerçek tam ekran modunu açıp kapatır, Esc gerçek tam ekrandan çıkar.

1. `Demo Veri Yükle` butonuna basın.
2. `Simülasyonu Başlat` butonuna basın.
3. Yolcular sırayla işlenirken bagajlar X-ray dedektöründen geçer.
4. Yasaklı eşya veya kara liste durumunda alarm sonucu gösterilir.
5. Simülasyon bitince `Raporu Göster` ile uygulama içi raporu açabilir veya `TXT Rapor Kaydet` ile dosyaya aktarabilirsiniz.

## Dosya yapısı

```text
Bagaj_Guvenlik_Simulatoru/
├── main.py
├── gui.py
├── simulator.py
├── passenger.py
├── linked_list.py
├── constants.py
├── sound_utils.py
├── assets/
│   ├── icon.ico
│   ├── icon.png
│   └── sounds/
│       ├── normal.wav
│       └── alarm.wav
├── README.md
└── reports/
```

## Pencere ve EXE ikonu

Programın pencere ikonu `assets/icon.ico` dosyasından alınır. Windows dışındaki bazı ortamlarda daha uyumlu görünmesi için `assets/icon.png` dosyası da yedek olarak eklenmiştir.

EXE üretirken aynı ikonun EXE dosyasına da işlenmesi için PyInstaller komutuna şu bölüm eklenmelidir:

```bash
--icon "assets\icon.ico"
```

Örnek final komut:

```bash
pyinstaller --noconfirm --clean --onefile --windowed --name "BagajGuvenlikSimulatoru" --icon "assets\icon.ico" --add-data "assets;assets" main.py
```

## Ses dosyaları

Program iki ses dosyası kullanır:

- `assets/sounds/normal.wav`: temiz geçiş sesi
- `assets/sounds/alarm.wav`: yasaklı eşya, kara liste veya diğer riskli sonuç sesi

Kendi seslerinizi kullanmak isterseniz aynı klasördeki dosyaları aynı isimlerle değiştirebilirsiniz. Ses dosyaları bulunamazsa program Windows üzerinde basit bip sesiyle yedekli çalışır.

## Notlar

- `__pycache__` klasörü teslim paketine eklenmemiştir.
- `winsound` bağımlılığı güvenli hale getirilmiştir. Windows dışındaki sistemlerde program hata vermeden çalışır.
- Raporlar `reports/` klasörüne kaydedilir.
- X-ray animasyonu dışarıdan görsel dosyası kullanmaz; tamamen Tkinter Canvas ile çizilir.
- Önceki sürümde tam ekranda sabit koordinatlar nedeniyle X-ray görüntüsü orantısız kalabiliyordu; bu sürümde canvas genişliğine göre yeniden çizim yapılır.
- Önceki sürümde pencere küçültülünce paneller sıkışabiliyordu; bu sürümde minimum içerik genişliği ve otomatik kaydırma sistemi eklendi.

## EXE oluşturma

Windows üzerinde en kolay yöntem:

1. Bu klasördeki `build_exe.bat` dosyasına çift tıklayın.
2. İşlem tamamlanınca EXE dosyası şu konumda oluşur:

```text
dist\BagajGuvenlikSimulatoru.exe
```

Bu script PyInstaller kurulu değilse otomatik kurar, eski build klasörlerini temizler, ikon ve ses dosyalarını EXE içine dahil eder.

Program açılmazsa `build_exe_debug.bat` dosyasını çalıştırın. Bu sürüm konsol penceresiyle açıldığı için hata mesajı görülebilir.

Manuel final komut:

```bat
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "BagajGuvenlikSimulatoru" --icon "assets\icon.ico" --add-data "assets;assets" --add-data "reports;reports" main.py
```

