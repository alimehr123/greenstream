# desktop_app.py  --- GreenStream Desktop (cross-OS ready)
import sys, os, platform, threading, time, requests

# --- Ensure root path in sys.path for shared_config import ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from shared_config import get_base_url  # unified config for all clients

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock, mainthread
from kivy.core.window import Window


# ---------- OS detection ----------
def detect_os():
    system_name = platform.system().lower()
    release = platform.release()
    return {
        "system": system_name,
        "release": release,
        "is_windows": system_name == "windows",
        "is_linux": system_name == "linux",
        "is_mac": system_name == "darwin",
    }

OS_INFO = detect_os()
EXTRA_NOTE = (
    "🧩 Running on Windows Desktop" if OS_INFO["is_windows"]
    else "🐧 Running on Linux" if OS_INFO["is_linux"]
    else "🍎 Running on macOS" if OS_INFO["is_mac"]
    else "💻 Unknown desktop OS"
)

API_URL = f"{get_base_url()}/hello"


# ---------- Helper ----------
def _is_spyder():
    return 'spyder' in sys.executable.lower() or 'spyder' in sys.argv[0].lower()


# ---------- UI ----------
class GreenStreamDesktopUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=15, **kwargs)

        self.label = Label(
            text=f"🌿 GreenStream Desktop\nDetected: {EXTRA_NOTE}\nPress to contact API.",
            font_size='18sp',
            halign='center'
        )
        self.add_widget(self.label)

        self.fetch_button = Button(text="Fetch Hello", size_hint=(1, 0.3))
        self.fetch_button.bind(on_press=self.fetch_hello_from_api)
        self.add_widget(self.fetch_button)

        self.exit_button = Button(text="Exit", size_hint=(1, 0.3))
        self.exit_button.bind(on_press=self.safe_exit)
        self.add_widget(self.exit_button)

        self.active_thread = None

    # ---------- API Thread ----------
    def fetch_hello_from_api(self, instance):
        self.label.text = "⏳ Contacting API server..."
        self.fetch_button.disabled = True
        self.active_thread = threading.Thread(target=self._thread_api_request, daemon=True)
        self.active_thread.start()

    def _thread_api_request(self):
        try:
            response = requests.get(API_URL, timeout=5)
            if response.status_code == 200:
                msg = response.json().get("message", "No message from server")
                self.update_label_success(msg)
            else:
                self.update_label_error(f"HTTP {response.status_code}")
        except Exception as e:
            self.update_label_error(str(e))

    @mainthread
    def update_label_success(self, msg):
        self.label.text = f"✅ Server says:\n{msg}\n({EXTRA_NOTE})"
        self.fetch_button.disabled = False

    @mainthread
    def update_label_error(self, err):
        self.label.text = f"❌ Error:\n{err}\n({EXTRA_NOTE})"
        self.fetch_button.disabled = False

    # ---------- Safe Exit ----------
    def safe_exit(self, *args):
        """Reliable exit for all environments: Spyder, CMD, and exe."""
        from kivy.app import App
        import threading, os
    
        # Disable UI interaction
        self.label.text = "👋 Closing GreenStream...\nPlease wait..."
        self.fetch_button.disabled = True
        self.exit_button.disabled = True
    
        # Wait briefly for any active thread
        if hasattr(self, "active_thread") and self.active_thread and self.active_thread.is_alive():
            try:
                self.active_thread.join(timeout=0.8)
            except Exception:
                pass
    
        def killer():
            """Kill‑guard: ensure full shutdown even if Kivy loop hangs."""
            time.sleep(0.6)  # short delay to let App.stop run
            try:
                os._exit(0)
            except Exception:
                pass
    
        # Start killer daemon thread
        threading.Thread(target=killer, daemon=True).start()
    
        # Try graceful stop
        def do_stop(dt):
            try:
                App.get_running_app().stop()
            except Exception:
                pass
        Clock.schedule_once(do_stop, 0)


# ---------- App ----------
class GreenStreamDesktopApp(App):
    def build(self):
        ui = GreenStreamDesktopUI()
        Window.bind(on_request_close=lambda *a: ui.safe_exit())
        self.title = f"GreenStream Desktop 🌿 ({OS_INFO['system'].capitalize()})"
        return ui


# ---------- Run ----------
if __name__ == "__main__":
    GreenStreamDesktopApp().run()
