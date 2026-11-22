@echo off
setlocal enabledelayedexpansion
title GTA 6 PS Remote Play Canli Cevirici

:: Python kontrolu
set "PYTHON_EXE="

python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where python') do (
        echo "%%i" | findstr /i "WindowsApps" >nul
        if errorlevel 1 (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
    )
)

if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    ) else if exist "%ProgramFiles%\Python312\python.exe" (
        set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
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

:: Program basariyla veya carpiya basilarak kapandiginda cmd penceresini de otomatik kapat
if %errorlevel% equ 0 exit /b 0

if %errorlevel% neq 0 (
    echo.
    echo Bir hata olustu. Eksik paketler olabilir.
    echo Lutfen 'Kurulum_Sihirbazi.bat' dosyasini calistirin.
    pause
)
