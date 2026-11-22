#!/bin/bash
cd "$(dirname "$0")"

# macOS izin hatalarini onlemek icin model dizinini proje icine yonlendir
export XDG_DATA_HOME="$(pwd)/models_data/share"
export XDG_CONFIG_HOME="$(pwd)/models_data/config"
export XDG_CACHE_HOME="$(pwd)/models_data/cache"

# Temel paketler kurulu mu kontrol et, eksikse otomatik kur
python3 -c "import mss, deep_translator, rapidocr_onnxruntime, PIL, numpy, AppKit" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[+] Ilk kullanim: Gerekli yapay zeka paketleri otomatik kuruluyor, lutfen bekleyin..."
    python3 -m pip install -r requirements.txt
fi

python3 gta_ceviri.py

# Uygulama kapandiktan sonra terminal penceresini de otomatik kapat
osascript -e 'tell application "Terminal"
    repeat with w in windows
        try
            if name of w contains "baslat_mac" then
                close w
            end if
        end try
    end repeat
    if (count of windows) = 0 then quit
end tell' 2>/dev/null &

exit 0
