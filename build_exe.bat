@echo off
chcp 65001 >nul
setlocal

TITLE Bagaj Güvenlik Simülatörü - EXE Oluşturma

echo.
echo ============================================================
echo  Bagaj Guvenlik Simulatoru - EXE Olusturma
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [HATA] Python bulunamadi. Once Python 3 kurulu olmali.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] PyInstaller kontrol ediliyor...
python -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller kurulu degil. Kuruluyor...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [HATA] PyInstaller kurulumu basarisiz oldu.
        pause
        exit /b 1
    )
) else (
    echo PyInstaller zaten kurulu.
)

echo.
echo [2/4] Eski build dosyalari temizleniyor...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist BagajGuvenlikSimulatoru.spec del /q BagajGuvenlikSimulatoru.spec

echo.
echo [3/4] EXE olusturuluyor...
python -m PyInstaller ^
 --noconfirm ^
 --clean ^
 --onefile ^
 --windowed ^
 --name "BagajGuvenlikSimulatoru" ^
 --icon "assets\icon.ico" ^
 --add-data "assets;assets" ^
 --add-data "reports;reports" ^
 main.py

if errorlevel 1 (
    echo.
    echo [HATA] EXE olusturma basarisiz oldu.
    echo Hatayi gormek icin build_exe_debug.bat dosyasini calistirabilirsin.
    pause
    exit /b 1
)

echo.
echo [4/4] Islem tamamlandi.
echo.
echo EXE dosyasi burada:
echo dist\BagajGuvenlikSimulatoru.exe
echo.
echo Program acilmazsa build_exe_debug.bat ile konsollu surumu olusturup hatayi gorebilirsin.
echo.
pause
endlocal
