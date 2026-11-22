import os
import sys
import json
import subprocess
import site
import importlib
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# macOS ve Linux üzerinde ~/.local izin hatalarını (PermissionError) önlemek için:
# Model ve veri dizinlerini doğrudan proje klasörüne yönlendiriyoruz
BASE_DIR = Path(__file__).resolve().parent
MODELS_DATA_DIR = BASE_DIR / "models_data"
MODELS_DATA_DIR.mkdir(parents=True, exist_ok=True)

os.environ["XDG_DATA_HOME"] = str(MODELS_DATA_DIR / "share")
os.environ["XDG_CONFIG_HOME"] = str(MODELS_DATA_DIR / "config")
os.environ["XDG_CACHE_HOME"] = str(MODELS_DATA_DIR / "cache")

# Stanza'nın her çeviride internete bağlanmaya çalışmasını önle (%100 çevrimdışı ve hızlı çalışsın)
try:
    import stanza
    _orig_stanza_init = stanza.Pipeline.__init__
    def _offline_stanza_init(self, *args, **kwargs):
        kwargs["download_method"] = None
        _orig_stanza_init(self, *args, **kwargs)
    stanza.Pipeline.__init__ = _offline_stanza_init
except Exception:
    pass

# Gerekli Temel Paketler:
# pip3 install mss deep-translator rapidocr_onnxruntime Pillow numpy
# İsteğe bağlı yerel çevrimdışı model için:
# pip3 install argostranslate

class GameSubtitleTranslator:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA 6 / PS Remote Play - Yapay Zeka Çevirici")
        self.root.geometry("490x490")
        self.root.attributes("-topmost", True)

        self.is_running = False
        self.last_detected_text = ""
        self.last_seen_time = 0
        self.current_duration = 3.5

        # Koordinatları yükle (Kullanıcı önceden kaydettiyse hatırlar)
        self.load_settings()

        # Çeviri Motoru: "google" veya "local_argos"
        self.engine_choice = tk.StringVar(value="local_argos")
        self.local_model_ready = False

        self.setup_ui()
        # Arka planda yerel modelin kurulu olup olmadığını kontrol et
        threading.Thread(target=self.check_local_model, daemon=True).start()

    def load_settings(self):
        self.roi = {"top": 750, "left": 350, "width": 800, "height": 110}
        # Varsayılan olarak Türkçe çeviri konumu doğrudan İngilizce altyazının üstüne yerleşir
        self.overlay_pos = {"top": 750, "left": 350, "width": 800, "height": 110}
        self.custom_overlay_set = False
        config_file = BASE_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "roi" in data:
                        self.roi.update(data["roi"])
                    if "overlay_pos" in data:
                        self.overlay_pos.update(data["overlay_pos"])
                        self.custom_overlay_set = True
            except Exception:
                pass

    def save_settings(self):
        config_file = BASE_DIR / "config.json"
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"roi": self.roi, "overlay_pos": self.overlay_pos}, f, indent=4)
        except Exception:
            pass

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

        # 1. Konum Ayarları Grubu
        area_frame = ttk.LabelFrame(frame, text="Ekran & Konum Ayarları", padding=8)
        area_frame.pack(fill=tk.X, pady=6)

        btn_roi = ttk.Button(
            area_frame, 
            text="🎯 1. Oyun Altyazı Okuma Alanı (Kırmızı Kutu)", 
            command=self.open_roi_selector
        )
        btn_roi.pack(fill=tk.X, pady=2)

        btn_overlay = ttk.Button(
            area_frame, 
            text="💬 2. Çeviri Yazı Konumunu Ayarla (Mavi Kutu)", 
            command=self.open_overlay_selector
        )
        btn_overlay.pack(fill=tk.X, pady=2)

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

        # 3. Başlat / Durdur
        self.btn_toggle = ttk.Button(frame, text="▶️ 3. Canlı Çeviriyi Başlat", command=self.toggle_translation)
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

    def _install_pip_package(self, package_name):
        """Kullanıcının terminale girmesine gerek kalmadan arka planda pip paketini otomatik kurar."""
        cmds = [
            [sys.executable, "-m", "pip", "install", package_name],
            [sys.executable, "-m", "pip", "install", "--user", package_name],
            [sys.executable, "-m", "pip", "install", "--break-system-packages", package_name]
        ]
        
        for cmd in cmds:
            try:
                proc = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True, 
                    timeout=300
                )
                if proc.returncode == 0:
                    try:
                        site.main()
                        user_site = site.getusersitepackages()
                        if user_site and user_site not in sys.path:
                            sys.path.insert(0, user_site)
                        importlib.invalidate_caches()
                    except Exception:
                        pass
                    return True
            except Exception:
                continue
        return False

    def ensure_core_dependencies(self):
        """Temel çeviri paketlerini (OCR, ekran yakalama vs.) kontrol eder, eksik varsa otomatik kurar."""
        missing = []
        checks = [
            ("mss", "mss"),
            ("deep_translator", "deep-translator"),
            ("rapidocr_onnxruntime", "rapidocr-onnxruntime"),
            ("PIL", "Pillow"),
            ("numpy", "numpy")
        ]
        for mod, pkg in checks:
            try:
                __import__(mod)
            except ImportError:
                missing.append(pkg)

        if not missing:
            return True

        self.status_var.set(f"Durum: Gerekli paketler otomatik yükleniyor: {', '.join(missing)}...")
        for pkg in missing:
            self._install_pip_package(pkg)

        # Tekrar kontrol et
        still_missing = []
        for mod, pkg in checks:
            try:
                __import__(mod)
            except ImportError:
                still_missing.append(pkg)
        return len(still_missing) == 0

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
        except Exception:
            self.local_model_ready = False

    def start_download_local_model(self):
        threading.Thread(target=self._download_local_model_thread, daemon=True).start()

    def _download_local_model_thread(self):
        self.root.after(0, lambda: self.btn_download_model.config(text="⏳ Hazırlanıyor...", state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set("Durum: Paket kontrol ediliyor..."))

        # 1. argostranslate kütüphanesi kurulu mu? Değilse arka planda otomatik kur
        try:
            import argostranslate.package
            import argostranslate.translate
        except ImportError:
            self.root.after(0, lambda: self.btn_download_model.config(text="⏳ Yapay Zeka Paketi Kuruluyor...", state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set("Durum: argostranslate kütüphanesi otomatik kuruluyor (Lütfen bekleyin)..."))

            success = self._install_pip_package("argostranslate")
            if not success:
                self.root.after(0, lambda: messagebox.showerror(
                    "Otomatik Kurulum Hatası", 
                    "argostranslate paketi otomatik kurulamadı.\nLütfen internet bağlantınızı kontrol edip tekrar deneyin."
                ))
                self.root.after(0, lambda: self.btn_download_model.config(text="📥 Yerel Modeli İndir (~150 MB - Tek Seferlik)", state=tk.NORMAL))
                self.root.after(0, lambda: self.status_var.set("Hata: Kütüphane kurulumu başarısız."))
                return

            try:
                import argostranslate.package
                import argostranslate.translate
            except ImportError:
                self.root.after(0, lambda: messagebox.showerror(
                    "Yeniden Başlatma Gerekli", 
                    "Paket başarıyla kuruldu! Değişikliğin algılanması için lütfen uygulamayı bir kez kapatıp tekrar açın."
                ))
                self.root.after(0, lambda: self.btn_download_model.config(text="Uygulamayı Yeniden Başlatın", state=tk.NORMAL))
                return

        # 2. Model dosyasını indir ve kur
        self.root.after(0, lambda: self.btn_download_model.config(text="⏳ Model İndiriliyor... (~150 MB)", state=tk.DISABLED))
        self.root.after(0, lambda: self.status_var.set("Durum: Açık kaynak çeviri modeli indiriliyor (~150 MB)..."))

        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            pkg = next((p for p in available_packages if p.from_code == "en" and p.to_code == "tr"), None)
            if pkg:
                download_path = pkg.download()
                argostranslate.package.install_from_path(download_path)
                self.local_model_ready = True
                self.root.after(0, lambda: self.btn_download_model.config(text="✅ Yerel Model Yüklü & Hazır", state=tk.DISABLED))
                self.root.after(0, lambda: self.status_var.set("Durum: Yerel model hazır! Çeviriyi başlatabilirsin."))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Tebrikler!",
                    "Açık kaynak yerel yapay zeka çeviri modeli başarıyla kuruldu!\nArtık '2. Canlı Çeviriyi Başlat' butonuna basarak tamamen çevrimdışı oynayabilirsiniz."
                ))
            else:
                self.root.after(0, lambda: self.status_var.set("Hata: en->tr dil paketi bulunamadı."))
                self.root.after(0, lambda: self.btn_download_model.config(text="Tekrar Dene", state=tk.NORMAL))
                self.root.after(0, lambda: messagebox.showerror("Hata", "Argos sunucusunda İngilizce->Türkçe dil paketi bulunamadı."))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"İndirme hatası: {e}"))
            self.root.after(0, lambda: self.btn_download_model.config(text="Tekrar Dene", state=tk.NORMAL))
            self.root.after(0, lambda: messagebox.showerror("İndirme Hatası", f"Model indirilirken bir hata oluştu:\n{e}"))

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
            # Kullanıcı özel bir mavi kutu ayarlamadıysa Türkçe altyazı varsayılan olarak İngilizce yazının tam üstüne otursun
            if not getattr(self, 'custom_overlay_set', False):
                self.overlay_pos = dict(self.roi)
            self.save_settings()
            self.status_var.set(f"Okuma Alanı Kaydedildi: {self.roi['width']}x{self.roi['height']}")
            self.selector_win.destroy()

        self.selector_win.protocol("WM_DELETE_WINDOW", save_and_close)

    def open_overlay_selector(self):
        self.overlay_selector_win = tk.Toplevel(self.root)
        self.overlay_selector_win.title("Çeviri Konumu (Türkçe yazının görünmesini istediğin yere taşı)")
        self.overlay_selector_win.geometry(f"{self.overlay_pos['width']}x{self.overlay_pos['height']}+{self.overlay_pos['left']}+{self.overlay_pos['top']}")
        self.overlay_selector_win.attributes("-alpha", 0.60)
        self.overlay_selector_win.attributes("-topmost", True)
        self.overlay_selector_win.config(bg="#0066ff")

        lbl = tk.Label(
            self.overlay_selector_win, 
            text="💬 Türkçe Çeviri Altyazısı Bu Kutunun İçinde Görünecektir.\nBu mavi kutuyu ekranda istediğin yere sürükle ve boyutlandır.\nİşin bitince bu pencereyi kapat.", 
            fg="white", 
            bg="#0066ff", 
            font=("Helvetica", 11, "bold")
        )
        lbl.pack(expand=True)

        def save_and_close():
            self.overlay_pos["left"] = self.overlay_selector_win.winfo_x()
            self.overlay_pos["top"] = self.overlay_selector_win.winfo_y()
            self.overlay_pos["width"] = self.overlay_selector_win.winfo_width()
            self.overlay_pos["height"] = self.overlay_selector_win.winfo_height()
            self.custom_overlay_set = True
            self.save_settings()
            self.status_var.set(f"Çeviri Konumu Kaydedildi: {self.overlay_pos['width']}x{self.overlay_pos['height']}")
            self.overlay_selector_win.destroy()

        self.overlay_selector_win.protocol("WM_DELETE_WINDOW", save_and_close)

    def _exclude_window_from_capture(self, window):
        """macOS ve Windows üzerinde çeviri penceresini ekran yakalamadan gizler.
        Böylece Türkçe altyazı doğrudan İngilizce altyazının tam üstüne basılsa dahi
        OCR oyundaki İngilizce altyazıyı kesintisiz okumaya devam edebilir."""
        try:
            if sys.platform == "darwin":
                import ctypes
                import ctypes.util
                objc = ctypes.cdll.LoadLibrary(ctypes.util.find_library("objc"))
                objc.objc_getClass.restype = ctypes.c_void_p
                objc.objc_getClass.argtypes = [ctypes.c_char_p]
                objc.sel_registerName.restype = ctypes.c_void_p
                objc.sel_registerName.argtypes = [ctypes.c_char_p]
                objc.objc_msgSend.restype = ctypes.c_void_p

                NSApplication = objc.objc_getClass(b"NSApplication")
                objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
                sharedApp = objc.objc_msgSend(NSApplication, objc.sel_registerName(b"sharedApplication"))
                windows = objc.objc_msgSend(sharedApp, objc.sel_registerName(b"windows"))

                count = objc.objc_msgSend(windows, objc.sel_registerName(b"count"))
                for i in range(count):
                    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
                    w = objc.objc_msgSend(windows, objc.sel_registerName(b"objectAtIndex:"), i)
                    # 0 = NSWindowSharingNone (ekran yakalamada görünmez)
                    objc.objc_msgSend.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong]
                    objc.objc_msgSend(w, objc.sel_registerName(b"setSharingType:"), 0)
            elif sys.platform == "win32":
                import ctypes
                hwnd = window.winfo_id()
                # WDA_EXCLUDEFROMCAPTURE = 0x00000011 (Windows 10 2004+)
                ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, 0x00000011)
        except Exception:
            pass

    def _compute_box_size(self, text, font_obj, max_width=850, pad_x=22, pad_y=10):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            if font_obj.measure(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []
        if current_line:
            lines.append(" ".join(current_line))
        if not lines:
            return 0, 0, ""

        wrapped_text = "\n".join(lines)
        actual_width = max(font_obj.measure(line) for line in lines) + pad_x * 2
        line_height = font_obj.metrics("linespace")
        actual_height = (len(lines) * line_height) + pad_y * 2
        return actual_width, actual_height, wrapped_text

    def toggle_translation(self):
        if not self.is_running:
            # Temel paketler hazır mı kontrol et
            if not self.ensure_core_dependencies():
                messagebox.showerror(
                    "Eksik Paketler", 
                    "Temel çeviri paketleri yüklenemedi. Lütfen internet bağlantınızı kontrol edip tekrar deneyin."
                )
                return

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
            self.btn_toggle.config(text="▶️ 3. Canlı Çeviriyi Başlat")
            self.status_var.set("Durum: Durduruldu")
            if hasattr(self, 'overlay') and self.overlay:
                self.overlay.destroy()

    def create_overlay_window(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.92)
        self.overlay.config(bg="#111111")

        self.sub_label = tk.Label(
            self.overlay, 
            text="", 
            font=("Helvetica", 17, "bold"), 
            fg="#FFE600",
            bg="#111111",
            justify=tk.CENTER
        )
        self.sub_label.pack(expand=True, fill=tk.BOTH, padx=12, pady=6)

        self._exclude_window_from_capture(self.overlay)
        # Başlangıçta gizle: Ekranda konuşma/yazı yokken kesinlikle hiçbir kutu görünmemeli!
        self.overlay.withdraw()

    def _show_subtitle(self, text):
        if not (hasattr(self, 'overlay') and self.overlay and self.is_running):
            return
        clean_text = text.strip() if text else ""
        if not clean_text:
            self._hide_subtitle()
            return

        from tkinter import font
        font_obj = font.Font(family="Helvetica", size=17, weight="bold")

        # Kullanıcının belirlediği alan genişliğine göre dinamik max sınır
        max_w = max(400, min(self.overlay_pos.get('width', 800), 950))
        box_w, box_h, wrapped_text = self._compute_box_size(clean_text, font_obj, max_width=max_w)
        if not wrapped_text:
            self._hide_subtitle()
            return

        self.sub_label.config(text=wrapped_text)

        # Yatayda merkezleme: Kullanıcının belirlediği kutunun yatay ortasına tam otur
        center_x = self.overlay_pos['left'] + (self.overlay_pos['width'] // 2)
        new_left = max(0, center_x - (box_w // 2))

        # Dikeyde merkezleme: İngilizce altyazının tam üstüne oturması için dikeyde ortala
        center_y = self.overlay_pos['top'] + (self.overlay_pos['height'] // 2)
        new_top = max(0, center_y - (box_h // 2))

        self.overlay.geometry(f"{box_w}x{box_h}+{new_left}+{new_top}")
        self._exclude_window_from_capture(self.overlay)
        self.overlay.deiconify()

    def _hide_subtitle(self):
        if hasattr(self, 'overlay') and self.overlay:
            self.sub_label.config(text="")
            self.overlay.withdraw()

    def _calculate_display_duration(self, text):
        """Kullanıcı deneyimi için altyazının ekranda kalma süresini metin uzunluğuna göre dinamik hesaplar.
        Netflix/film standartlarına uygun ortalama okuma hızını (15 karakter/sn) esas alır."""
        if not text:
            return 3.0
        char_count = len(text.strip())
        # Taban süre: 2.8 saniye (gözün odaklanıp algılaması için)
        # Karakter başına ~0.065 saniye ek süre
        duration = 2.8 + (char_count * 0.065)
        # En az 3.0 saniye, en fazla 7.5 saniye ekranda tut
        return min(max(duration, 3.0), 7.5)

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
                                # Metin uzunluğuna göre dinamik ekranda kalma süresini belirle
                                self.current_duration = self._calculate_display_duration(translated)
                                self.root.after(0, lambda t=translated: self._show_subtitle(t))
                            except Exception:
                                pass

                    # Metin uzunluğuna göre hesaplanan süre dolduysa ve yeni konuşma yoksa kutuyu gizle
                    if time.time() - self.last_seen_time > self.current_duration and self.last_detected_text != "":
                        self.root.after(0, self._hide_subtitle)
                        self.last_detected_text = ""

                    time.sleep(0.18)

                except Exception:
                    time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameSubtitleTranslator(root)
    root.mainloop()
