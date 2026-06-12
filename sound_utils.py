"""İki sonuç tipi için platforma uygun ses yardımcıları.

- normal.wav: temiz geçiş
- alarm.wav : yasaklı eşya, kara liste veya diğer riskli sonuçlar

Ses dosyaları `assets/sounds/` klasöründe aranır. Dosya bulunamazsa Windows'ta
basit bip yedeği kullanılır; Windows dışındaki sistemlerde terminal alarmı veya
uygun sistem oynatıcısı denenir.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOUND_DIR = BASE_DIR / "assets" / "sounds"
NORMAL_SOUND = SOUND_DIR / "normal.wav"
ALARM_SOUND = SOUND_DIR / "alarm.wav"

try:
    import winsound  # type: ignore[attr-defined]
except ImportError:  # Windows dışındaki sistemlerde winsound yoktur.
    winsound = None


def _sistem_oynatici_ile_cal(dosya: Path) -> bool:
    """Windows dışı sistemlerde mevcutsa basit sistem oynatıcılarını dener."""
    if not dosya.exists():
        return False

    komutlar = [
        ["afplay", str(dosya)],  # macOS
        ["paplay", str(dosya)],  # Linux / PulseAudio
        ["aplay", str(dosya)],   # Linux / ALSA
    ]
    for komut in komutlar:
        if shutil.which(komut[0]):
            try:
                subprocess.Popen(komut, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
    return False


def _wav_cal(dosya: Path) -> bool:
    """Varsa WAV dosyasını çalar."""
    if not dosya.exists():
        return False

    if winsound:
        try:
            winsound.PlaySound(str(dosya), winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        except Exception:
            return False

    return _sistem_oynatici_ile_cal(dosya)


def sonuc_sesi_cal(kotu_sonuc: bool) -> None:
    """Temiz geçişte normal sesi, riskli geçişte alarm sesini bir kez çalar."""
    ses_dosyasi = ALARM_SOUND if kotu_sonuc else NORMAL_SOUND
    if _wav_cal(ses_dosyasi):
        return

    # Yedek ses: ses dosyası yoksa veya çalınamazsa hata vermeden devam eder.
    if winsound:
        if kotu_sonuc:
            winsound.Beep(520, 450)
        else:
            winsound.Beep(900, 120)
    else:
        print("\a", end="")


# Eski kodlarla uyumluluk için bırakıldı.
def alarm_sesi_cal() -> None:
    sonuc_sesi_cal(kotu_sonuc=True)
