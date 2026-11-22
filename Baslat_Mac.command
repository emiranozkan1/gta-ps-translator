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

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Bir hata olustu. Pencereyi kapatmak icin herhangi bir tusa basin..."
    read -n 1
fi
