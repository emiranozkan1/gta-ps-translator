import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Gerekli Temel Paketler:
# pip3 install mss deep-translator rapidocr_onnxruntime Pillow numpy
# İsteğe bağlı yerel çevrimdışı model için:
# pip3 install argostranslate

class GameSubtitleTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA 6 / PS Remote Play - Yapay Zeka Çevirici")
        self.root.geometry("480x420")
        self.root.attributes("-topmost", True)

        self.is_running = False
        self.last_detected_text = ""
        self.last_seen_time = 0

        # Varsayılan Altyazı Koordinatları (Kullanıcı değiştirebilir)
        self.roi = {"top": 750, "left": 350, "width": 800, "height": 110}

        # Çeviri Motoru: "google" veya "local_argos"
        self.engine_choice = tk.StringVar(value="local_argos")
        self.local_model_ready = False

        self.setup_ui()
        # Arka planda yerel modelin kurulu olup olmadığını kontrol et
        threading.Thread(target=self.check_local_model, daemon=True).start()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = ttk.Label(frame, text="🎮 PS5 Canlı Altyazı Çevirici", font=("Helvetica", 15, "bold"))
        lbl_title.pack(pady=4)

        lbl_desc = ttk.Label(
            frame, 
            text="PS Remote Play'deki İngilizce altyazıyı yapay zekayla anında Türkçe yapar.",
            font=("Helvetica", 10),
            foreground="#555555"
        )
        lbl_desc.pack(pady=2)

        # 1. Altyazı Bölgesi Butonu
        btn_box = ttk.Button(frame, text="🎯 1. Altyazı Alanını Ayarla (Kutuyu Yerleştir)", command=self.open_roi_selector)
        btn_box.pack(fill=tk.X, pady=8)

        # Motor Seçimi Grubu
        engine_frame = ttk.LabelFrame(frame, text="Çeviri Yapay Zekası", padding=10)
        engine_frame.pack(fill=tk.X, pady=6)

        rb_local = ttk.Radiobutton(
            engine_frame, 
            text="🧠 Açık Kaynak Yerel Model (CTranslate2 / Argos) - %100 Çevrimdışı", 
            variable=self.engine_choice, 
            value="local_argos"
        )
        rb_local.pack(anchor=tk.W, pady=2)

        rb_cloud = ttk.Radiobutton(
            engine_frame, 
            text="⚡ Google NMT (Sıfır Kurulum, Anında Hazır)", 
            variable=self.engine_choice, 
            value="google"
        )
        rb_cloud.pack(anchor=tk.W, pady=2)

        self.btn_download_model = ttk.Button(
            engine_frame, 
            text="📥 Yerel Modeli İndir (~150 MB - Tek Seferlik)", 
            command=self.start_download_local_model
        )
        self.btn_download_model.pack(fill=tk.X, pady=4)

        # 2. Başlat / Durdur
        self.btn_toggle = ttk.Button(frame, text="▶️ 2. Canlı Çeviriyi Başlat", command=self.toggle_translation)
        self.btn_toggle.pack(fill=tk.X, pady=8)

        # Durum Çubuğu
        self.status_var = tk.StringVar(value="Durum: Hazır")
        lbl_status = ttk.Label(frame, textvariable=self.status_var, font=("Helvetica", 10, "italic"), foreground="#0066cc")
        lbl_status.pack(pady=4)

        # İpucu
        lbl_tip = ttk.Label(
            frame, 
            text="💡 İpucu: GTA ayarlarından 'Subtitle Background: On' (Altyazı Arka Planı: Açık) yaparsan çeviri %100 kusursuz okur.",
            font=("Helvetica", 9),
            foreground="#666666",
            wraplength=440
        )
        lbl_tip.pack(pady=4)

    def check_local_model(self):
        try:
            import argostranslate.package
            import argostranslate.translate
            installed = argostranslate.translate.get_installed_languages()
            from_lang = next((l for l in installed if l.code == "en"), None)
            to_lang = next((l for l in installed if l.code == "tr"), None)
            if from_lang and to_lang and from_lang.get_translation(to_lang):
                self.local_model_ready = True
                self.root.after(0, lambda: self.btn_download_model.config(text="✅ Yerel Model Yüklü & Hazır", state=tk.DISABLED))
                self.root.after(0, lambda: self.status_var.set("Durum: Açık kaynak yerel model hazır."))
            else:
                self.local_model_ready = False
        except ImportError:
            self.local_model_ready = False

    def start_download_local_model(self):
        threading.Thread(target=self._download_local_model_thread, daemon=True).start()

    def _download_local_model_thread(self):
        try:
            import argostranslate.package
            import argostranslate.translate
        except ImportError:
            self.root.after(0, lambda: messagebox.showerror(
                "Eksik Paket", 
                "Lütfen Terminalde şu komutu çalıştır:\npip3 install argostranslate"
            ))
            return

        self.root.after(0, lambda: self.btn_download_model.config(text="⏳ Model İndiriliyor... (~150 MB)", state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set("Durum: Açık kaynak çeviri modeli indiriliyor..."))

        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            pkg = next((p for p in available_packages if p.from_code == "en" and p.to_code == "tr"), None)
            if pkg:
                download_path = pkg.download()
                argostranslate.package.install_from_path(download_path)
                self.local_model_ready = True
                self.root.after(0, lambda: self.btn_download_model.config(text="✅ Model Başarıyla Kuruldu", state=tk.DISABLED))
                self.root.after(0, lambda: self.status_var.set("Durum: Yerel model hazır! Çeviriyi başlatabilirsin."))
            else:
                self.root.after(0, lambda: self.status_var.set("Hata: en->tr dil paketi bulunamadı."))
                self.root.after(0, lambda: self.btn_download_model.config(text="Tekrar Dene", state=tk.NORMAL))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"İndirme hatası: {e}"))
            self.root.after(0, lambda: self.btn_download_model.config(text="Tekrar Dene", state=tk.NORMAL))

    def open_roi_selector(self):
        self.selector_win = tk.Toplevel(self.root)
        self.selector_win.title("Altyazı Alanı (Bu kırmızı kutuyu oyun altyazısının üstüne yerleştir)")
        self.selector_win.geometry(f"{self.roi['width']}x{self.roi['height']}+{self.roi['left']}+{self.roi['top']}")
        self.selector_win.attributes("-alpha", 0.45)
        self.selector_win.attributes("-topmost", True)
        self.selector_win.config(bg="red")

        lbl = tk.Label(
            self.selector_win, 
            text="Bu kırmızı kutuyu PS Remote Play'deki altyazının tam üstüne sürükleyip boyutlandır.\nİşin bitince bu pencereyi kapat.", 
            fg="white", 
            bg="red", 
            font=("Helvetica", 12, "bold")
        )
        lbl.pack(expand=True)

        def save_and_close():
            self.roi["left"] = self.selector_win.winfo_x()
            self.roi["top"] = self.selector_win.winfo_y()
            self.roi["width"] = self.selector_win.winfo_width()
            self.roi["height"] = self.selector_win.winfo_height()
            self.status_var.set(f"Alan Kaydedildi: {self.roi['width']}x{self.roi['height']}")
            self.selector_win.destroy()

        self.selector_win.protocol("WM_DELETE_WINDOW", save_and_close)

    def toggle_translation(self):
        if not self.is_running:
            # Yerel model seçilmiş ama indirilmemişse uyar
            if self.engine_choice.get() == "local_argos" and not self.local_model_ready:
                res = messagebox.askyesno(
                    "Yerel Model Hazır Değil",
                    "Açık kaynak yerel model henüz indirilmedi.\n"
                    "Şimdilik hızlı Google NMT ile başlatılsın mı?"
                )
                if res:
                    self.engine_choice.set("google")
                else:
                    return

            self.is_running = True
            self.btn_toggle.config(text="⏹️ Çeviriyi Durdur")
            engine_name = "Yerel Açık Kaynak Model" if self.engine_choice.get() == "local_argos" else "Google NMT"
            self.status_var.set(f"Aktif: {engine_name} ile canlı taranıyor...")
            self.create_overlay_window()
            threading.Thread(target=self.translation_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="▶️ 2. Canlı Çeviriyi Başlat")
            self.status_var.set("Durum: Durduruldu")
            if hasattr(self, 'overlay') and self.overlay:
                self.overlay.destroy()

    def create_overlay_window(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.90)

        overlay_y = max(20, self.roi["top"] - 75)
        overlay_w = max(self.roi['width'], 650)
        self.overlay.geometry(f"{overlay_w}x70+{self.roi['left']}+{overlay_y}")
        self.overlay.config(bg="#111111")

        self.sub_text = tk.StringVar(value="[GTA Canlı Çeviri Aktif - Konuşma Bekleniyor]")
        self.sub_label = tk.Label(
            self.overlay, 
            textvariable=self.sub_text, 
            font=("Helvetica", 17, "bold"), 
            fg="#FFE600",
            bg="#111111",
            wraplength=overlay_w - 20,
            justify=tk.CENTER
        )
        self.sub_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    def translation_loop(self):
        import mss
        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR

        ocr = RapidOCR()

        # Motor başlatma
        google_trans = None
        argos_trans = None

        if self.engine_choice.get() == "local_argos":
            try:
                import argostranslate.translate
                installed = argostranslate.translate.get_installed_languages()
                from_lang = next((l for l in installed if l.code == "en"), None)
                to_lang = next((l for l in installed if l.code == "tr"), None)
                if from_lang and to_lang:
                    argos_trans = from_lang.get_translation(to_lang)
            except Exception:
                argos_trans = None

        if argos_trans is None:
            from deep_translator import GoogleTranslator
            google_trans = GoogleTranslator(source='en', target='tr')

        with mss.mss() as sct:
            while self.is_running:
                try:
                    monitor = {
                        "top": self.roi["top"],
                        "left": self.roi["left"],
                        "width": self.roi["width"],
                        "height": self.roi["height"]
                    }
                    screenshot = sct.grab(monitor)
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    img_np = np.array(img)

                    result, _ = ocr(img_np)
                    if result:
                        lines = [line[1].strip() for line in result if line[1].strip()]
                        detected_text = " ".join(lines).replace("\n", " ").strip()

                        if len(detected_text) >= 3 and detected_text.lower() != self.last_detected_text.lower():
                            self.last_detected_text = detected_text
                            self.last_seen_time = time.time()

                            # Çeviri uygula
                            try:
                                if argos_trans:
                                    translated = argos_trans.translate(detected_text)
                                else:
                                    translated = google_trans.translate(detected_text)
                                self.sub_text.set(translated)
                            except Exception:
                                pass

                    # 6 saniye yeni ses/yazı yoksa ekranı temizle
                    if time.time() - self.last_seen_time > 6 and self.last_detected_text != "":
                        self.sub_text.set("")
                        self.last_detected_text = ""

                    time.sleep(0.18)

                except Exception:
                    time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameSubtitleTranslator(root)
    root.mainloop()
