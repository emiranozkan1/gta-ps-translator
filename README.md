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

## 🍏 Hızlı Başlatma (macOS)

Mac kullanıyorsanız terminalle uğraşmanıza gerek yoktur:
- Klasördeki **`Baslat_Mac.command`** dosyasına çift tıklayarak uygulamayı başlatabilirsiniz.
- Eksik paketler veya yapay zeka çeviri modeli varsa program arka planda bunları otomatik olarak kuracaktır.

---

## 🚀 Özellikler

- **Çift Yapay Zeka Motoru:**
  - 🧠 **Açık Kaynak Yerel Model (CTranslate2 / Argos):** %100 yerel ve çevrimdışı çalışır. İnternet gerektirmez, kota/ücret yoktur.
  - ⚡ **Google NMT:** Sıfır indirme gerektiren anında hazır bulut çevirisi.
- **Ultra Hızlı OCR (RapidOCR / ONNX):** Ekrandaki altyazıyı 15-20 milisaniyede algılar.
- **Çift Dinamik Bölge Seçimi:** Ekrana gelen kırmızı kutuyu oyunun İngilizce altyazısına, mavi kutuyu ise Türkçe çevirinin çıkmasını istediğiniz konuma sürükleyip bırakabilirsiniz. Konumlar otomatik kaydedilir.
- **Akıllı Dilbilgisi & Cümle Birleştirme (SVO ➔ SOV Uyumu):** İngilizce (Özne-Yüklem-Nesne) ve Türkçe (Özne-Nesne-Yüklem) arasındaki dilbilgisi farkını hesaba katar. Ekrana parça parça gelen yarım cümleleri (virgüllü veya bağlaçlı geçişleri) akıllıca birleştirip tam, anlamlı ve %100 doğal bir Türkçe cümle olarak çevirir.
- **Dinamik Kutu Boyutu & Okuma Süresi:** Altyazı kutusu metnin uzunluğuna göre dinamik büyür/küçülür. Ekranda kalma süresi de harf sayısına göre otomatik hesaplanır (kısa sözler hızla kalkar, uzun cümleler rahatça okunur).
- **Akıllı Otomatik Gizleme (Oyun Deneyimini Korur):** Ekranda konuşma veya altyazı yokken arayüz tamamen görünmez olur, siyah kutu ekranda kalmaz. Sadece konuşma olduğunda zarifçe belirir.

---

## 🎮 En Yüksek Doğruluk İçin Oyun İçi Ayar

GTA veya oynadığınız oyunun görüntü/altyazı ayarlarından:
- **Subtitle Background (Altyazı Arka Planı):** `On / Opaque / Siyah` yapın.
- Bu ayar yapıldığında arkadaki patlamalar ve ışıklar yazıyı bozmaz, yapay zeka altyazıyı %100 kusursuz okur.
