#!/bin/bash
# Terminal penceresinin basligini ayarla
echo -n -e "\033]0;GTA 6 PS Remote Play Canli Cevirici\007"
cd "$(dirname "$0")"

echo "========================================================"
echo "  GTA 6 / PS Remote Play Canli Cevirici Baslatiliyor..."
echo "========================================================"

python3 gta_ceviri.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[!] Bir hata olustu. Terminaldeki paket indirmelerinin tamamlandigindan emin olun."
    echo "Pencereyi kapatmak icin herhangi bir tusa basin..."
    read -n 1
fi
