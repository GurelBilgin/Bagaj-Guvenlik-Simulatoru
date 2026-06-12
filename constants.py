"""Bagaj Güvenlik Simülatörü genel sabitleri."""

# Sistemin tehlikeli kabul ettiği tüm yasaklı eşyalar tek yerde tutulur.
# Böylece yolcu üretimi, bagaj taraması ve raporlama aynı listeyi kullanır.
YASAKLI_ESYALAR = (
    "bıçak",
    "silah",
    "patlayıcı",
    "aerosol",
    "yanıcı madde",
)

ZARARSIZ_ESYALAR = (
    "kitap",
    "telefon",
    "şarj aleti",
    "çorap",
    "parfüm",
    "tablet",
    "laptop",
    "şemsiye",
    "kulaklık",
    "defter",
)

# Demo veride kara liste mantığının görülebilmesi için başlangıçta
# riskli kabul edilen örnek yolcu ID'leri.
BASLANGIC_KARA_LISTE = (
    "P-RISK-001",
    "P-RISK-002",
)
