@echo off
title GTA 6 Cevirici - Bagimlilik Kurulumu
echo ========================================================
echo   Gerekli yapay zeka paketleri yukleniyor...
echo   Lutfen indirmeler bitene kadar bekleyin.
echo ========================================================
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [HATA] Paketler yuklenirken bir sorun olustu.
    echo Python'in kurulu oldugundan ve internet baglantinizdan emin olun.
    pause
    exit /b
)
echo.
echo ========================================================
echo   [BASARILI] Tum bagimliliklar yuklendi!
echo   Simdi 'baslat_windows.bat' dosyasina cift tiklayabilirsiniz.
echo ========================================================
pause
