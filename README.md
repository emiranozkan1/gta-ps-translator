# 🎮 GTA 6 / PS Remote Play Canlı Altyazı Çevirici (AI Subtitle Translator)

PlayStation 5 oyunlarını (özellikle resmi Türkçe dil desteği olmayan GTA 6 gibi oyunları) **PS Remote Play** ile bilgisayara aktarırken, ekrandaki İngilizce altyazıyı yapay zeka ile gerçek zamanlı olarak Türkçe'ye çevirip ekran üstüne şık bir arayüzle yansıtan açık kaynaklı bir araçtır.

Hem **Windows** hem de **macOS** ile %100 uyumludur.

---

## 🚀 Özellikler

- **Çift Yapay Zeka Motoru:**
  - 🧠 **Açık Kaynak Yerel Model (CTranslate2 / Argos):** %100 yerel ve çevrimdışı çalışır. İnternet gerektirmez, kota/ücret yoktur.
  - ⚡ **Google NMT:** Sıfır indirme gerektiren anında hazır bulut çevirisi.
- **Ultra Hızlı OCR (RapidOCR / ONNX):** Ekrandaki altyazıyı 15-20 milisaniyede algılar.
- **Dinamik Bölge Seçimi:** Ekrana gelen kırmızı kutuyu PS Remote Play altyazı alanına sürükleyip bırakmanız yeterlidir.
- **Oyun İçi HUD / Şeffaf Arayüz:** Oyunun üzerinde yarı saydam, sarı renkli GTA tarzı yüksek kontrastlı altyazı gösterir.
- **Akıllı Filtreleme:** Aynı metni tekrar tekrar çevirmez, sessizlik olduğunda altyazıyı otomatik temizler.

---

## 🛠️ Kurulum

### Windows (Ana Bilgisayar):
1. Python'ın kurulu olduğundan emin olun ([python.org](https://www.python.org/) üzerinden indirirken *"Add Python to PATH"* kutucuğunu işaretleyin).
2. Proje dizininde komut istemcisini (CMD veya PowerShell) açın:
   ```cmd
   pip install -r requirements.txt
   ```
3. Başlatmak için `baslat_windows.bat` dosyasına çift tıklayın veya:
   ```cmd
   python gta_ceviri.py
   ```

### macOS:
1. Terminali açın:
   ```bash
   pip3 install -r requirements.txt
   python3 gta_ceviri.py
   ```

---

## 🎮 En Yüksek Doğruluk İçin Oyun İçi Ayar

GTA veya oynadığınız oyunun görüntü/altyazı ayarlarından:
- **Subtitle Background (Altyazı Arka Planı):** `On / Opaque / Siyah` yapın.
- Bu ayar yapıldığında arkadaki patlamalar ve ışıklar yazıyı bozmaz, yapay zeka altyazıyı %100 kusursuz okur.
