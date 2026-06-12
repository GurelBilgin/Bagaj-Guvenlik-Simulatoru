"""Kara liste için basit bağlı liste veri yapısı."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass
class Node:
    yolcu_id: str
    next: Optional["Node"] = None


class LinkedList:
    """Tek yönlü bağlı liste.

    Bu proje kapsamında kara listedeki yolcu ID'lerini tutmak için kullanılır.
    Aynı ID'nin tekrar eklenmesi engellenir.
    """

    def __init__(self) -> None:
        self.head: Optional[Node] = None

    def ekle(self, yolcu_id: str) -> bool:
        """ID listede yoksa başa ekler. Eklendiyse True döner."""
        if self.kontrol(yolcu_id):
            return False
        self.head = Node(yolcu_id=yolcu_id, next=self.head)
        return True

    def kontrol(self, yolcu_id: str) -> bool:
        """Belirtilen ID kara listede var mı?"""
        current = self.head
        while current:
            if current.yolcu_id == yolcu_id:
                return True
            current = current.next
        return False

    def sil(self, yolcu_id: str) -> bool:
        """Belirtilen ID'yi listeden siler. Silindiyse True döner."""
        current = self.head
        previous: Optional[Node] = None

        while current:
            if current.yolcu_id == yolcu_id:
                if previous:
                    previous.next = current.next
                else:
                    self.head = current.next
                return True
            previous = current
            current = current.next

        return False

    def temizle(self) -> None:
        self.head = None

    def listele(self) -> list[str]:
        return list(iter(self))

    def uzunluk(self) -> int:
        return sum(1 for _ in self)

    def __iter__(self) -> Iterator[str]:
        current = self.head
        while current:
            yield current.yolcu_id
            current = current.next

    def __len__(self) -> int:
        return self.uzunluk()
