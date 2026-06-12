"""Yolcu modelini ve örnek yolcu üretimini içerir."""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import ClassVar

from constants import YASAKLI_ESYALAR, ZARARSIZ_ESYALAR


@dataclass
class Passenger:
    gorunen_ad: str
    unique_id: str
    bagaj: list[str] = field(default_factory=list)

    id_counter: ClassVar[int] = 1

    @classmethod
    def rastgele_olustur(cls, yasakli_esya_olasiligi: float = 0.10) -> "Passenger":
        """Rastgele bagaja sahip yeni yolcu üretir."""
        yolcu_no = cls.id_counter
        cls.id_counter += 1

        toplam_esya = random.randint(5, 10)
        bagaj: list[str] = []

        for _ in range(toplam_esya):
            if random.random() < yasakli_esya_olasiligi:
                bagaj.append(random.choice(YASAKLI_ESYALAR))
            else:
                bagaj.append(random.choice(ZARARSIZ_ESYALAR))

        return cls(
            gorunen_ad=f"Yolcu #{yolcu_no}",
            unique_id=f"P-{str(uuid.uuid4())[:8].upper()}",
            bagaj=bagaj,
        )

    @classmethod
    def demo_yolcular(cls) -> list["Passenger"]:
        """Hocaya gösterim ve test için sonucu öngörülebilir örnek yolcular."""
        yolcular = [
            cls("Demo Temiz Yolcu", "P-DEMO-001", ["kitap", "telefon", "şarj aleti", "çorap"]),
            cls("Demo Bıçak Yakalanan", "P-DEMO-002", ["kitap", "bıçak", "telefon"]),
            cls("Demo Kara Listedeki", "P-RISK-001", ["laptop", "defter", "kulaklık"]),
            cls("Demo Aerosol Yakalanan", "P-DEMO-003", ["tablet", "aerosol", "şemsiye"]),
            cls("Demo Yanıcı Madde", "P-DEMO-004", ["çorap", "yanıcı madde", "telefon"]),
            cls("Demo Patlayıcı Yakalanan", "P-DEMO-005", ["kitap", "patlayıcı", "kulaklık"]),
            cls("Demo Silah Yakalanan", "P-RISK-002", ["telefon", "silah", "defter"]),
        ]

        # Demo veriden sonra rastgele yolcu numaraları karışmasın.
        cls.id_counter = max(cls.id_counter, len(yolcular) + 1)
        return yolcular

    def __str__(self) -> str:
        return f"{self.gorunen_ad} | {self.unique_id} | {len(self.bagaj)} eşya"
