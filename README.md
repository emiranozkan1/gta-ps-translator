# 🎮 GTA 6 / PS Remote Play Canlı Altyazı Çevirici (AI Subtitle Translator)

PlayStation 5 oyunlarını (özellikle resmi Türkçe dil desteği olmayan GTA 6 gibi oyunları) **PS Remote Play** ile bilgisayara aktarırken, ekrandaki İngilizce altyazıyı yapay zeka ile gerçek zamanlı olarak Türkçe'ye çevirip ekran üstüne şık bir arayüzle yansıtan açık kaynaklı bir araçtır.

Hem **Windows** hem de **macOS** ile %100 uyumludur.

---

## ⚡ Hızlı Kurulum (Windows - Tek Tıkla Kurulum Sihirbazı)

Windows bilgisayarınızda **Python yüklü olmasa bile** hiçbir şeyle uğraşmanıza gerek yoktur:

1. Repoyu indirin (**Code -> Download ZIP**) ve bir klasöre çıkartın.
2. Klasördeki **`Kurulum_Sihirbazi.bat`** dosyasına çift tıklayın.
   * Bu sihirbaz bilgisayarınızda Python yoksa resmi 64-bit Python'ı otomatik indirip kurar, PATH ayarını yapar.
   * Gerekli tüm yapay zeka ve OCR kütüphanelerini yükler.
   * Masaüstünüze **"GTA 6 Canlı Çevirici"** kısayolunu otomatik ekler!
3. Artık oyunu her açtığınızda masaüstündeki kısayola tıklamanız yeterlidir.

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

## 🎮 En Yüksek Doğruluk İçin Oyun İçi Ayar

GTA veya oynadığınız oyunun görüntü/altyazı ayarlarından:
- **Subtitle Background (Altyazı Arka Planı):** `On / Opaque / Siyah` yapın.
- Bu ayar yapıldığında arkadaki patlamalar ve ışıklar yazıyı bozmaz, yapay zeka altyazıyı %100 kusursuz okur.
