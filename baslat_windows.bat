@echo off
setlocal enabledelayedexpansion
title GTA 6 PS Remote Play Canli Cevirici
color 0E

:: Python kontrolu
set "PYTHON_EXE="

where python >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
) else (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    )
)

if not defined PYTHON_EXE (
    echo [HATA] Python bulunamadi!
    echo Lutfen once 'Kurulum_Sihirbazi.bat' dosyasini calistirin.
    pause
    exit /b 1
)

echo ========================================================
echo   GTA 6 / PS Remote Play Canli Cevirici Baslatiliyor...
echo ========================================================

"%PYTHON_EXE%" "%~dp0gta_ceviri.py"

if errorlevel 1 (
    echo.
    echo Bir hata olustu. Eksik paketler olabilir.
    echo Lutfen 'Kurulum_Sihirbazi.bat' dosyasini calistirin.
    pause
)
