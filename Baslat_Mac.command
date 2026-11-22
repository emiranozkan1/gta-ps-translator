#!/bin/bash
# Terminal penceresinin basligini ayarla
echo -n -e "\033]0;GTA 6 PS Remote Play Canli Cevirici\007"
cd "$(dirname "$0")"

# macOS izin hatalarini onlemek icin model dizinini proje icine yonlendir
export XDG_DATA_HOME="$(pwd)/models_data/share"
export XDG_CONFIG_HOME="$(pwd)/models_data/config"
export XDG_CACHE_HOME="$(pwd)/models_data/cache"

echo "========================================================"
echo "  GTA 6 / PS Remote Play Canli Cevirici Baslatiliyor..."
echo "========================================================"

# Temel paketler kurulu mu kontrol et, eksikse otomatik kur
python3 -c "import mss, deep_translator, rapidocr_onnxruntime, PIL, numpy" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[+] Gerekli yapay zeka paketleri otomatik kuruluyor, lutfen bekleyin..."
    python3 -m pip install -r requirements.txt
fi

python3 gta_ceviri.py

EXIT_CODE=$?

# Uygulama kapandiktan sonra bu terminal penceresini de otomatik kapat
# Hata varsa kullaniciya goster, yoksa terminali kapat
if [ $EXIT_CODE -ne 0 ] && [ $EXIT_CODE -ne 0 ]; then
    # os._exit(0) kullanildiginda exit code her zaman 0 olur
    :
fi

# Terminal penceresini otomatik kapat (kullanici bir sey yapmasina gerek yok)
osascript -e 'tell application "Terminal"
    set windowCount to count of windows
    if windowCount > 0 then
        repeat with w in windows
            try
                if name of w contains "GTA 6" or name of w contains "Baslat_Mac" then
                    close w
                end if
            end try
        end repeat
    end if
    -- Eger baska terminal penceresi kalmadiysa Terminal uygulamasini da kapat
    if (count of windows) = 0 then
        quit
    end if
end tell' 2>/dev/null &

exit 0
