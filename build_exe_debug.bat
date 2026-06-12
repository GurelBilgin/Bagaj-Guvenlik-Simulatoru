@echo off
chcp 65001 >nul
setlocal

TITLE Bagaj Güvenlik Simülatörü - Debug EXE Oluşturma

echo.
echo ============================================================
echo  Bagaj Guvenlik Simulatoru - DEBUG EXE Olusturma
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Once Python 3 kurulu olmali.
    pause
    exit /b 1
)

python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller kurulu degil. Kuruluyor...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [HATA] PyInstaller kurulumu basarisiz oldu.
        pause
        exit /b 1
    )
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BagajGuvenlikSimulatoru.spec del /q BagajGuvenlikSimulatoru.spec

echo Konsollu DEBUG EXE olusturuluyor...
echo Bu surumde hata varsa siyah ekranda gorunur.

python -m PyInstaller ^
 --noconfirm ^
 --clean ^
 --onefile ^
 --name "BagajGuvenlikSimulatoru_DEBUG" ^
 --icon "assets\icon.ico" ^
 --add-data "assets;assets" ^
 --add-data "reports;reports" ^
 main.py

if errorlevel 1 (
    echo.
    echo [HATA] Debug EXE olusturma basarisiz oldu.
    pause
    exit /b 1
)

echo.
echo DEBUG EXE dosyasi burada:
echo dist\BagajGuvenlikSimulatoru_DEBUG.exe
echo.
pause
endlocal
