"""Bagaj Güvenlik Simülatörü giriş dosyası."""

from gui import BagajGuvenlikApp


def main() -> None:
    app = BagajGuvenlikApp()
    app.mainloop()


if __name__ == "__main__":
    main()
