import os
import io
import threading
import webbrowser
from datetime import datetime
import requests

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen, ScreenManager

from kivymd.app import MDApp
from kivymd.uix.button import MDFillRoundFlatButton, MDRaisedButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField

# ---------- CONFIG ----------
API_URL = "https://api.waifu.im/search?included_tags=ero"
DOWNLOAD_DIR = "/storage/emulated/0/Download/justscriptz"
TIMEOUT = 15

ALLOWED_USERNAME = "aryan"
ALLOWED_PASSWORD = "1234"
GITHUB_LINK = "https://github.com/xitebanned-byte"

# ---------- LOGIN SCREEN ----------
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(
            orientation="vertical",
            padding=40,
            spacing=25,
            size_hint=(0.8, 0.6),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )

        layout.add_widget(MDLabel(
            text="🔐 Login to Continue",
            halign="center",
            font_style="H5",
            bold=True
        ))

        self.username = MDTextField(
            hint_text="Enter Username",
            size_hint_x=1
        )
        layout.add_widget(self.username)

        self.password = MDTextField(
            hint_text="Enter Password",
            password=True,
            size_hint_x=1
        )
        layout.add_widget(self.password)

        self.msg = MDLabel(
            text="",
            halign="center",
            theme_text_color="Error"
        )
        layout.add_widget(self.msg)

        login_btn = MDRaisedButton(
            text="Login",
            pos_hint={"center_x": 0.5}
        )
        login_btn.bind(on_press=self.check_login)
        layout.add_widget(login_btn)

        self.add_widget(layout)

    def check_login(self, *args):
        u = self.username.text.strip()
        p = self.password.text.strip()
        if u == ALLOWED_USERNAME and p == ALLOWED_PASSWORD:
            MDApp.get_running_app().root.current = "waifu"
        else:
            self.msg.text = "❌ Invalid credentials"

# ---------- WAIFU SCREEN ----------
class WaifuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        app = MDApp.get_running_app()
        app.current_img_data = None
        app.current_img_ext = "jpg"
        app.img_history = []
        app.history_index = -1

        root = BoxLayout(orientation="vertical", spacing=6)

        # Toolbar with separate About and GitHub buttons
        self.toolbar = MDTopAppBar(
            title="Waifu Viewer 💜",
            pos_hint={"top": 1},
            elevation=10,
        )
        self.toolbar.left_action_items = [["information-outline", lambda x: self.show_about()]]
        self.toolbar.right_action_items = [["github", lambda x: self.open_github()]]
        root.add_widget(self.toolbar)

        # Image card
        app.card = MDCard(
            orientation="vertical",
            size_hint=(1, 0.8),
            padding=10,
            radius=[20, 20, 20, 20],
            elevation=15,
        )

        app.img_widget = Image(
            size_hint=(1, 1),
        )
        app.card.add_widget(app.img_widget)
        root.add_widget(app.card)

        # Buttons row
        btn_row = BoxLayout(size_hint=(1, 0.12), spacing=15, padding=10)
        app.prev_btn = MDFillRoundFlatButton(text="⬅ Prev", on_release=self.show_prev)
        app.refresh_btn = MDFillRoundFlatButton(text="⟳ Refresh", on_release=self.fetch_new)
        app.next_btn = MDFillRoundFlatButton(text="Next ➡", on_release=self.show_next)
        app.download_btn = MDFillRoundFlatButton(text="⬇ Download", on_release=self.download_img)

        btn_row.add_widget(app.prev_btn)
        btn_row.add_widget(app.refresh_btn)
        btn_row.add_widget(app.next_btn)
        btn_row.add_widget(app.download_btn)
        root.add_widget(btn_row)

        # Status label
        app.status = MDLabel(
            text="Ready",
            halign="center",
            theme_text_color="Hint",
            font_style="H6",
            size_hint=(1, 0.05),
        )
        root.add_widget(app.status)

        self.add_widget(root)
        Clock.schedule_once(lambda dt: self.fetch_new(), 0.3)

    def set_status(self, text):
        MDApp.get_running_app().status.text = text

    # ---------- Image Fetching ----------
    def fetch_new(self, *args):
        self.set_status("Fetching waifu... 💫")
        t = threading.Thread(target=self.fetch_thread, daemon=True)
        t.start()

    def fetch_thread(self):
        try:
            r = requests.get(API_URL, timeout=TIMEOUT)
            r.raise_for_status()
            js = r.json()
            img_url = js.get("images", [{}])[0].get("url")
            if not img_url:
                raise Exception("No image found")
            r2 = requests.get(img_url, timeout=TIMEOUT)
            r2.raise_for_status()
            data = r2.content
            ext = "jpg" if "jpeg" in r2.headers.get("Content-Type", "") else "png"

            app = MDApp.get_running_app()
            app.current_img_data = data
            app.current_img_ext = ext
            app.img_history = app.img_history[:app.history_index+1]
            app.img_history.append((data, ext))
            app.history_index += 1

            Clock.schedule_once(lambda dt: self.update_img(), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_status(f"Error: {e}"), 0)

    def update_img(self):
        app = MDApp.get_running_app()
        data = io.BytesIO(app.current_img_data)
        app.img_widget.texture = CoreImage(data, ext=app.current_img_ext).texture
        self.set_status("Waifu loaded! 💜 (⬇ to save)")

    # ---------- History ----------
    def show_prev(self, *args):
        app = MDApp.get_running_app()
        if app.history_index > 0:
            app.history_index -= 1
            app.current_img_data, app.current_img_ext = app.img_history[app.history_index]
            self.update_img()

    def show_next(self, *args):
        app = MDApp.get_running_app()
        if app.history_index < len(app.img_history)-1:
            app.history_index += 1
            app.current_img_data, app.current_img_ext = app.img_history[app.history_index]
            self.update_img()

    # ---------- Download ----------
    def download_img(self, *args):
        app = MDApp.get_running_app()
        if not app.current_img_data:
            self.set_status("No image to download")
            return
        t = threading.Thread(target=self.save_thread, daemon=True)
        t.start()

    def save_thread(self):
        app = MDApp.get_running_app()
        try:
            if not os.path.isdir(DOWNLOAD_DIR):
                os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            fname = f"waifu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{app.current_img_ext}"
            path = os.path.join(DOWNLOAD_DIR, fname)
            with open(path, "wb") as f:
                f.write(app.current_img_data)
            Clock.schedule_once(lambda dt: self.set_status(f"Saved ✅: {path}"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.set_status(f"Save error: {e}"), 0)

    # ---------- Menu Actions ----------
    def show_about(self):
        self.set_status("Made by xitebanned-byte")

    def open_github(self):
        webbrowser.open(GITHUB_LINK)

# ---------- APP ----------
class ImageViewer(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.theme_style = "Dark"
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(WaifuScreen(name="waifu"))
        self.sm.current = "login"
        return self.sm

if __name__ == "__main__":
    ImageViewer().run()