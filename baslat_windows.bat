@echo off
title GTA 6 PS Remote Play Canli Cevirici
echo ========================================================
echo   GTA 6 / PS Remote Play Canli Cevirici Baslatiliyor...
echo ========================================================
python gta_ceviri.py
if errorlevel 1 (
    echo.
    echo Bir hata olustu. Python ve paketlerin kurulu oldugundan emin olun.
    pause
)
