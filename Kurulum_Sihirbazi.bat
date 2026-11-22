@echo off
setlocal enabledelayedexpansion
title GTA 6 PS Remote Play - Otomatik Kurulum Sihirbazi
color 0B

echo =======================================================================
echo    GTA 6 / PS Remote Play Canli Cevirici - Kurulum Sihirbazi
echo =======================================================================
echo.
echo Bu sihirbaz bilgisayarinizda gerekli her seyi (Python dahil)
echo otomatik olarak indirecek ve kuracaktir.
echo Hicbir teknik ayar yapmaniza gerek yoktur.
echo.
echo =======================================================================
pause

:: 1. ADIM: PYTHON KONTROLU
echo.
echo [1/3] Python kontrol ediliyor...

set "PYTHON_EXE="

:: Oncelikle PATH'teki python gercekten calisiyor mu ve WindowsApps tuzagi degil mi test et
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('where python') do (
        echo "%%i" | findstr /i "WindowsApps" >nul
        if errorlevel 1 (
            if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
        )
    )
    if defined PYTHON_EXE echo [+] Python zaten kurulu bulundu: !PYTHON_EXE!
)

:: PATH'te bulunamadiysa standart dizinlerde ara
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        echo [+] Python bulundu: !PYTHON_EXE!
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        echo [+] Python bulundu: !PYTHON_EXE!
    ) else if exist "%ProgramFiles%\Python312\python.exe" (
        set "PYTHON_EXE=%ProgramFiles%\Python312\python.exe"
        echo [+] Python bulundu: !PYTHON_EXE!
    )
)

:: Python bulunamadiysa otomatik indir ve kur
if not defined PYTHON_EXE (
    echo [-] Python bulunamadi!
    echo [+] Resmi Python 3.12 (64-bit) indiriliyor...
    
    set "INSTALLER=%TEMP%\python_installer.exe"
    
    :: PowerShell ile resmi python installer indir
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Indiriliyor, lutfen bekleyin...'; (New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe', '%INSTALLER%')"
    
    if not exist "%INSTALLER%" (
        echo [HATA] Python indirilemedi! Lutfen internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
    
    echo [+] Python arka planda sessizce kuruluyor ve PATH ayari yapiliyor...
    echo     (Bu islem 30-60 saniye surebilir, lutfen bekleyin)
    
    start /wait "" "%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Shortcuts=0
    del "%INSTALLER%" >nul 2>&1
    
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
        echo [+] Python basariyla kuruldu!
    ) else (
        echo [HATA] Python kurulumu tamamlanamadi.
        pause
        exit /b 1
    )
)

:: 2. ADIM: YAPAY ZEKA VE GEREKLI PAKETLERIN KURULUMU
echo.
echo =======================================================================
echo [2/3] Yapay zeka kutuphaneleri yukleniyor...
echo     (RapidOCR, CTranslate2/Argos, Ekran Yakalama vs.)
echo     Bu islem internet hizina bagli olarak 1-2 dakika surebilir.
echo =======================================================================
echo.

"%PYTHON_EXE%" -m pip install --upgrade pip
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt"

if %errorlevel% neq 0 (
    echo.
    echo [HATA] Kutuphaneler yuklenirken bir sorun olustu.
    pause
    exit /b 1
)

:: 3. ADIM: MASAUSTUNE KISAYOL EKLEME
echo.
echo [3/3] Masaustune kisayol olusturuluyor...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\GTA 6 Canli Cevirici.lnk'); $s.TargetPath = '%~dp0baslat_windows.bat'; $s.WorkingDirectory = '%~dp0'; $s.WindowStyle = 1; $s.Description = 'GTA 6 PS Remote Play Canli Altyazi Cevirici'; $s.Save()"

echo.
echo =======================================================================
echo    TEBRIKLER! HER SEY BASARIYLA KURULDU!
echo =======================================================================
echo.
echo  * Masaustunuze 'GTA 6 Canli Cevirici' kisayolu eklendi.
echo  * Artik oyunu her oynadiginizda masaustundeki o ikona tiklamaniz yeterli.
echo.
set /p BASLAT="Simdi ceviri uygulamasini baslatmak ister misiniz? (E/H): "
if /i "%BASLAT%"=="E" (
    start "" "%~dp0baslat_windows.bat"
)

exit /b 0
