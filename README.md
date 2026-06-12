# 🧳 Bagaj Güvenlik Simülatörü

Bu proje, bagaj güvenlik kontrol sürecini veri yapıları kullanarak simüle eden bir Python/Tkinter uygulamasıdır. Uygulamada yolcular sırayla güvenlik kontrolüne alınır, bagaj içerikleri stack mantığıyla taranır ve riskli yolcular kara listeye bağlı liste yapısıyla eklenir.

Programda X-ray dedektör animasyonu, konveyör bant görünümü, temiz/riskli geçiş sesleri, kara liste kontrolü ve gün sonu raporlama sistemi bulunmaktadır.

---

## 🎯 Proje Amacı

Bu uygulamanın amacı, temel veri yapılarının gerçek hayata benzer bir senaryo üzerinde nasıl kullanılabileceğini göstermektir.

Projede özellikle şu veri yapıları kullanılmıştır:

* Queue
* Stack
* Linked List

Bagaj güvenlik kontrolü senaryosu üzerinden yolcu kuyruğu, bagaj taraması ve kara liste takibi görsel bir arayüzle simüle edilmiştir.

---

## 🧠 Kullanılan Veri Yapıları

### Queue / deque

Yolcular güvenlik kontrolüne sırayla alınır. İlk gelen yolcu ilk kontrol edilir.

### Stack / list

Bagajdaki eşyalar LIFO mantığıyla taranır. Son eklenen eşya ilk kontrol edilir.

### Linked List

Kara listedeki yolcu ID kayıtları bağlı liste yapısıyla tutulur.

---

## ✨ Özellikler

* Rastgele yolcu üretme
* Demo veri yükleme
* Temiz, tehlikeli ve kara listedeki yolcuları simüle etme
* X-ray dedektör ve konveyör bant animasyonu
* Bagaj dedektörden geçerken eşya içeriğini görsel olarak gösterme
* Yasaklı eşyaları kırmızı, temiz eşyaları yeşil/mavi tonlarında gösterme
* Temiz geçişte normal ses çalma
* Yasaklı eşya veya kara liste durumunda alarm sesi çalma
* Kara listeye otomatik yolcu ekleme
* Önceden kara listede olan yolcuları yakalama
* Uygulama içinde gün sonu raporu görüntüleme
* İstenirse TXT rapor kaydetme
* Temiz geçiş oranı ve alarm oranı hesaplama
* Açılışta ekranı dolduran arayüz
* Pencere küçültülünce kaydırılabilir responsive yapı
* Özel pencere ve EXE ikonu desteği

---

## 🚫 Yasaklı Eşyalar

Yasaklı eşyalar `constants.py` dosyasında tek merkezden yönetilir.

Varsayılan yasaklı eşyalar:

* bıçak
* silah
* patlayıcı
* aerosol
* yanıcı madde

---

## 🖥️ Ekran ve Kullanım

Program açıldığında ekranı dolduracak şekilde başlar. Pencere moduna alındığında arayüz mümkün olduğu kadar yeniden ölçeklenir. Pencere çok daraltılırsa panellerin birbirine girmemesi için kaydırma sistemi devreye girer.

Kısayollar:

* `F11`: Tam ekran modunu açar/kapatır.
* `Esc`: Tam ekrandan çıkar.

Kullanım adımları:

1. `Demo Veri Yükle` butonuna basın.
2. `Simülasyonu Başlat` butonuna basın.
3. Yolcular sırayla güvenlik kontrolünden geçer.
4. Bagajlar X-ray dedektör animasyonu ile taranır.
5. Yasaklı eşya veya kara liste durumunda alarm sonucu gösterilir.
6. Simülasyon bitince `Raporu Göster` ile gün sonu raporu görüntülenebilir.

---

## 📁 Dosya Yapısı

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
├── reports/
├── build_exe.bat
├── build_exe_debug.bat
├── EXE_OLUSTURMA_NOTLARI.txt
└── README.md
```

---

## 🔊 Ses Sistemi

Program iki farklı ses kullanır:

* `assets/sounds/normal.wav`: Temiz geçiş sesi
* `assets/sounds/alarm.wav`: Yasaklı eşya, kara liste veya riskli durum sesi

Kendi ses dosyalarınızı kullanmak isterseniz aynı klasördeki dosyaları aynı isimlerle değiştirebilirsiniz.

Ses dosyaları bulunamazsa program Windows üzerinde yedek olarak basit bip sesiyle çalışır.

---

## 🖼️ Pencere ve EXE İkonu

Programın pencere ikonu `assets/icon.ico` dosyasından alınır.

Ayrıca `assets/icon.png` dosyası ikonun görsel kaynak/yedek hali olarak projede tutulmuştur.

EXE oluştururken aynı ikonun EXE dosyasına işlenmesi için PyInstaller komutunda şu bölüm kullanılır:

```bat
--icon "assets\icon.ico"
```

---

## ▶️ Çalıştırma

Python 3 yüklü olmalıdır.

Proje klasöründe terminal veya CMD açıp şu komutu çalıştırın:

```bat
python main.py
```

---

## 📦 EXE Oluşturma

Windows üzerinde en kolay yöntem:

1. Proje klasöründeki `build_exe.bat` dosyasına çift tıklayın.
2. İşlem tamamlandığında EXE dosyası şu konumda oluşur:

```text
dist\BagajGuvenlikSimulatoru.exe
```

Manuel EXE oluşturmak için:

```bat
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "BagajGuvenlikSimulatoru" --icon "assets\icon.ico" --add-data "assets;assets" --add-data "reports;reports" main.py
```

Program açılmazsa hata mesajını görmek için `build_exe_debug.bat` dosyası kullanılabilir.

---

## 📝 Raporlama

Simülasyon sonunda uygulama içinde gün sonu raporu görüntülenebilir.

Raporda şu bilgiler yer alır:

* İşlenen yolcu sayısı
* Kuyrukta bekleyen yolcu sayısı
* Alarm/yasaklı eşya sayısı
* Engellenen yolcu sayısı
* Temiz geçiş sayısı
* Kara liste kayıt sayısı
* Toplam bagaj/eşya sayısı
* Temiz geçiş oranı
* Alarm oranı

İstenirse rapor TXT dosyası olarak da kaydedilebilir.

---

## ⚙️ Teknik Notlar

* Arayüz Python Tkinter ile geliştirilmiştir.
* X-ray animasyonu Tkinter Canvas ile çizilmiştir.
* Harici görsel dosyasına ihtiyaç duymadan dedektör, konveyör bant ve bagaj animasyonu oluşturulur.
* `winsound` bağımlılığı güvenli hale getirilmiştir.
* Windows dışındaki sistemlerde ses sistemi hata vermeden devre dışı kalabilir.
* `__pycache__`, `build`, `dist` ve `.spec` dosyaları GitHub deposuna eklenmemelidir.

---

## 👨‍💻 Geliştirici

**Gürel Bilgin**

GitHub: `GurelBilgin`
