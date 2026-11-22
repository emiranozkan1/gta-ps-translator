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
    import stanza  # type: ignore[import-untyped]
    _orig_stanza_init = stanza.Pipeline.__init__
    def _offline_stanza_init(self_pipe, *args, **kwargs):  # noqa: N805
        kwargs["download_method"] = None
        _orig_stanza_init(self_pipe, *args, **kwargs)
    stanza.Pipeline.__init__ = _offline_stanza_init  # type: ignore[assignment]
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
        self.sentence_buffer = ""
        self.last_fragment_time = 0
        self.overlay = None
        self.sub_label = None

        # Koordinatları yükle (Kullanıcı önceden kaydettiyse hatırlar)
        self.load_settings()

        # Çeviri Motoru: "google" veya "local_argos"
        self.engine_choice = tk.StringVar(value="local_argos")
        self.local_model_ready = False

        self.setup_ui()

        # Pencere kapatıldığında tüm işlemleri temizle ve terminali de kapat
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # macOS Spaces / Full Screen ayarlarını ana pencereye de uygula
        self.root.after(300, lambda: self._setup_overlay_window_native(self.root))

        # Arka planda yerel modelin kurulu olup olmadığını kontrol et
        threading.Thread(target=self.check_local_model, daemon=True).start()

    def _on_close(self):
        """Uygulama kapatıldığında tüm thread'leri durdur, overlay'ı temizle ve Python sürecini tamamen sonlandır."""
        self.is_running = False
        if self.overlay:
            try:
                self.overlay.destroy()
            except Exception:
                pass
            self.overlay = None
        try:
            self.root.destroy()
        except Exception:
            pass
        # Tüm arka plan thread'leri daemon olduğu için process kapanınca otomatik ölür
        os._exit(0)

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
            text="🎯 1. Altyazı Alanını Ayarla (Kutuyu Yerleştir)", 
            command=self.open_roi_selector
        )
        btn_roi.pack(fill=tk.X, pady=2)

        btn_overlay = ttk.Button(
            area_frame, 
            text="💬 2. Çeviri Konumunu Ayarla (Opsiyonel)", 
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
        if sys.platform == "darwin":
            checks.append(("AppKit", "pyobjc-framework-Cocoa"))

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
            import argostranslate.package  # type: ignore[import-untyped]
            import argostranslate.translate  # type: ignore[import-untyped]
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
            import argostranslate.package  # type: ignore[import-untyped]
            import argostranslate.translate  # type: ignore[import-untyped]
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
                import argostranslate.package  # type: ignore[import-untyped]
                import argostranslate.translate  # type: ignore[import-untyped]  # type: ignore[import-untyped]
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
                    "Açık kaynak yerel yapay zeka çeviri modeli başarıyla kuruldu!\nArtık '3. Canlı Çeviriyi Başlat' butonuna basarak tamamen çevrimdışı oynayabilirsiniz."
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
            foreground="white", 
            background="red", 
            font=("Helvetica", 12, "bold")
        )
        lbl.pack(expand=True)
        self._setup_overlay_window_native(self.selector_win)

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
            foreground="white", 
            background="#0066ff", 
            font=("Helvetica", 11, "bold")
        )
        lbl.pack(expand=True)
        self._setup_overlay_window_native(self.overlay_selector_win)

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

    def _setup_overlay_window_native(self, window, exclude_from_capture=False):
        """macOS ve Windows üzerinde pencereyi oyun üstü (HUD / Game Overlay) moduna alır:
        1. Tam ekran oyunların (PS Remote Play) üzerinde görünmesini sağlar (FullScreenAuxiliary).
        2. TÜM Space/masaüstlerinde sabit kalır (CanJoinAllSpaces | Stationary) — hangi ekrana geçersen geç ekranda çakılı kalır.
        3. Odak çalmaz ve controller/klavye kontrollerini engellemez.
        4. exclude_from_capture=True ise ekran yakalamadan gizlenir (sadece çeviri overlay'ı için)."""
        if sys.platform == "darwin":
            try:
                window.update_idletasks()
                window.update()
                import AppKit  # type: ignore[import-untyped]

                # CanJoinAllSpaces (1) | Stationary (16) | FullScreenAuxiliary (256) | IgnoresCycle (64) = 337
                # Stationary (16) bayrağı: macOS Spaces geçişi sırasında pencerenin ekranda sabit kalmasını sağlar!
                behavior = (
                    AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
                    | AppKit.NSWindowCollectionBehaviorStationary
                    | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
                    | AppKit.NSWindowCollectionBehaviorIgnoresCycle
                )

                target_title = ""
                try:
                    target_title = window.title()
                except Exception:
                    pass

                ns_app = AppKit.NSApplication.sharedApplication()
                for w in ns_app.windows():
                    w_title = w.title()
                    match = False
                    if target_title and w_title == target_title:
                        match = True
                    elif not target_title and w.isVisible():
                        match = True
                    if w_title == "__GTA_OVERLAY__":
                        match = True

                    if match:
                        # 1. TÜM Space / Masaüstü / FullScreen ekranlarında çakılı kıl
                        w.setCollectionBehavior_(behavior)
                        # 2. Seviyeyi en üste çıkart (101: NSPopUpMenuWindowLevel - her şeyin üstünde)
                        w.setLevel_(AppKit.NSPopUpMenuWindowLevel)
                        # 3. Odak başka uygulamaya (Antigravity, PS Remote Play) geçtiğinde ASLA gizlenme
                        if hasattr(w, "setHidesOnDeactivate_"):
                            w.setHidesOnDeactivate_(False)
                        if hasattr(w, "setCanHide_"):
                            w.setCanHide_(False)
                        # 4. Kullanıcı başka bir ekrana geçtiğinde bile en öne çiz
                        if hasattr(w, "orderFrontRegardless"):
                            w.orderFrontRegardless()
                        # 5. Sadece çeviri overlay'ı ekran yakalamadan gizle
                        if exclude_from_capture and hasattr(w, "setSharingType_"):
                            w.setSharingType_(AppKit.NSWindowSharingNone)
            except Exception:
                pass

        elif sys.platform == "win32":
            try:
                import ctypes
                hwnd = window.winfo_id()
                if exclude_from_capture:
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
            if self.overlay:
                try:
                    self.overlay.destroy()
                except Exception:
                    pass
                self.overlay = None
                self.sub_label = None

    def create_overlay_window(self):
        self.overlay = tk.Toplevel(self.root)
        self.overlay.title("__GTA_OVERLAY__")
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        # Başlangıçta tamamen görünmez — yazı algılanana kadar hiçbir şey görünmez
        self.overlay.attributes("-alpha", 0.0)
        self.overlay.config(background="#111111")
        # Overlay penceresini baştan doğru koordinatlara yerleştir (alpha=0.0 ile görünmez)
        self.overlay.geometry(f"{self.overlay_pos['width']}x{self.overlay_pos['height']}+{self.overlay_pos['left']}+{self.overlay_pos['top']}")

        self.sub_label = tk.Label(
            self.overlay, 
            text="", 
            font=("Helvetica", 17, "bold"), 
            foreground="#FFE600",
            background="#111111",
            justify=tk.CENTER
        )
        self.sub_label.pack(expand=True, fill=tk.BOTH, padx=12, pady=6)

        # Pencereyi Cocoa ile senkronize et ve native Spaces/Stationary ayarlarını uygula
        self.overlay.update()
        self._setup_overlay_window_native(self.overlay, exclude_from_capture=True)
        self.root.after(100, lambda: self._setup_overlay_window_native(self.overlay, exclude_from_capture=True))

    def _show_subtitle(self, text):
        if not (self.overlay and self.sub_label and self.is_running):
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
        # Sadece opaklığı aç: Bu sayede macOS masaüstü değiştirmez, odak çalmaz
        self.overlay.attributes("-alpha", 0.92)
        # Aktif ekranda en öne çizilmesi için native overlay ayarlarını anında pekiştir
        self._setup_overlay_window_native(self.overlay, exclude_from_capture=True)

    def _hide_subtitle(self):
        if self.overlay:
            # Opaklığı 0 yapıp metni temizliyoruz (withdraw kullanmadan, böylece Space zıplaması asla olmaz)
            self.overlay.attributes("-alpha", 0.0)
            if self.sub_label:
                self.sub_label.config(text="")

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

    def _smart_merge_dialogue(self, new_text):
        """İngilizce ve Türkçe arasındaki dilbilgisel yapı farkını (Özne-Yüklem-Nesne vs. Özne-Nesne-Yüklem)
        hesaba katarak bölünmüş diyalogları akıllıca birleştirir."""
        conjunctions = {
            "and", "but", "or", "because", "so", "if", "when", "that", "which",
            "who", "where", "while", "though", "although", "to", "for", "with", "without",
            "as", "since", "until", "before", "after"
        }

        now = time.time()
        time_delta = now - self.last_fragment_time if self.last_fragment_time else 999
        self.last_fragment_time = now

        prev = self.sentence_buffer.strip()
        curr = new_text.strip()

        # 1. Eğer aradan 3.8 saniyeden fazla zaman geçtiyse eski cümle bitmiş demektir
        if not prev or time_delta > 3.8:
            self.sentence_buffer = curr
            return curr

        # 2. Oyun ekrana parça parça ekleme yapıyorsa (progressive subtitle)
        if curr.lower().startswith(prev.lower()):
            self.sentence_buffer = curr
            return curr

        # 3. Önceki parça nokta, ünlem veya soru işaretiyle bitmemişse (yarım cümle)
        prev_incomplete = not any(prev.endswith(p) for p in (".", "!", "?", '."', '!"', '?"'))

        # 4. Yeni parça küçük harfle başlıyorsa ya da bağlaç/devam işaretiyle başlıyorsa
        first_word = curr.split()[0].lower().strip(",.-") if curr.split() else ""
        curr_is_continuation = curr[0].islower() or (first_word in conjunctions) or curr.startswith("...") or curr.startswith("-")

        if prev_incomplete or curr_is_continuation:
            # İki parçayı akıcı bir şekilde birleştir
            merged = prev.rstrip(",-… ") + " " + curr.lstrip("-.… ")
            # Eğer birleşik cümle artık bittiyse buffer'ı temizle
            if any(merged.endswith(p) for p in (".", "!", "?", '."', '!"', '?"')):
                self.sentence_buffer = ""
            else:
                self.sentence_buffer = merged
            return merged
        else:
            # Bağımsız yeni bir cümle
            self.sentence_buffer = curr
            return curr

    def _preprocess_image(self, img_np):
        """OCR doğruluğunu artırmak için görüntüyü ön işleme tabi tutar.
        Kontrast artırma, gri tonlama ve eşikleme ile YouTube/oyun altyazılarını net okur."""
        import numpy as np  # type: ignore[import-untyped]
        
        # RGB -> Gri tonlama
        if len(img_np.shape) == 3:
            gray = np.dot(img_np[..., :3], [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        else:
            gray = img_np
        
        # Kontrast artırma (CLAHE benzeri basit histogram yayma)
        min_val, max_val = gray.min(), gray.max()
        if max_val > min_val:
            gray = ((gray - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        
        # Altyazılar genelde açık renklidir — parlak pikselleri vurgula
        # Adaptif eşikleme: 180 üzerini beyaz, altını siyah yap
        threshold = 150
        binary = np.where(gray > threshold, 255, 0).astype(np.uint8)
        
        # 3 kanala geri çevir (RapidOCR RGB bekler)
        result = np.stack([binary, binary, binary], axis=-1)
        return result

    def translation_loop(self):
        import mss  # type: ignore[import-untyped]
        import numpy as np  # type: ignore[import-untyped]
        from PIL import Image  # type: ignore[import-untyped]
        from rapidocr_onnxruntime import RapidOCR  # type: ignore[import-untyped]

        ocr = RapidOCR()

        # Motor başlatma
        google_trans = None
        argos_trans = None

        if self.engine_choice.get() == "local_argos":
            try:
                import argostranslate.translate  # type: ignore[import-untyped]
                installed = argostranslate.translate.get_installed_languages()
                from_lang = next((lang for lang in installed if lang.code == "en"), None)
                to_lang = next((lang for lang in installed if lang.code == "tr"), None)
                if from_lang and to_lang:
                    argos_trans = from_lang.get_translation(to_lang)
            except Exception:
                argos_trans = None

        if argos_trans is None:
            from deep_translator import GoogleTranslator  # type: ignore[import-untyped]
            google_trans = GoogleTranslator(source='en', target='tr')

        consecutive_empty = 0  # Üst üste boş tarama sayacı

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

                    # 1. İlk önce ham görüntüyle OCR dene
                    result, _ = ocr(img_np)
                    detected_text = ""
                    
                    if result:
                        lines = [line[1].strip() for line in result if line[1].strip()]
                        detected_text = " ".join(lines).replace("\n", " ").strip()
                    
                    # 2. Ham görüntüde bulamazsa, ön işlenmiş (kontrast artırılmış) görüntüyle tekrar dene
                    if len(detected_text) < 3:
                        processed_img = self._preprocess_image(img_np)
                        result2, _ = ocr(processed_img)
                        if result2:
                            lines2 = [line[1].strip() for line in result2 if line[1].strip()]
                            detected_text = " ".join(lines2).replace("\n", " ").strip()

                    if len(detected_text) >= 3 and detected_text.lower() != self.last_detected_text.lower():
                        self.last_detected_text = detected_text
                        self.last_seen_time = time.time()
                        consecutive_empty = 0

                        # Akıllı dilbilgisi birleştirmesi (İngilizce -> Türkçe cümle yapısı uyumu)
                        text_to_translate = self._smart_merge_dialogue(detected_text)

                        # Çeviri uygula
                        try:
                            if argos_trans:
                                translated = argos_trans.translate(text_to_translate)
                            else:
                                translated = google_trans.translate(text_to_translate)
                            # Metin uzunluğuna göre dinamik ekranda kalma süresini belirle
                            self.current_duration = self._calculate_display_duration(translated)
                            self.root.after(0, lambda t=translated: self._show_subtitle(t))
                        except Exception:
                            pass

                    elif len(detected_text) < 3:
                        consecutive_empty += 1

                    # Metin uzunluğuna göre hesaplanan süre dolduysa ve yeni konuşma yoksa kutuyu gizle
                    if time.time() - self.last_seen_time > self.current_duration and self.last_detected_text != "":
                        self.root.after(0, self._hide_subtitle)
                        self.last_detected_text = ""
                        self.sentence_buffer = ""

                    time.sleep(0.18)

                except Exception:
                    time.sleep(0.5)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameSubtitleTranslator(root)
    root.mainloop()
