import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
import threading
import os

import backend

class TaraApp(App):
    def build(self):
        self.title = "Tara Voice Assistant"
        self.icon = 'icon.png'

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Background
        with layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)  # Dark background
            self.rect = Rectangle(size=Window.size, pos=layout.pos)
            layout.bind(size=self._update_rect, pos=self._update_rect)

        # Title Label
        title_label = Label(
            text="Tara Voice Assistant",
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(title_label)

        # Image for status
        self.status_image = Image(
            source='images/listening.png',
            size_hint=(1, 0.6)
        )
        layout.add_widget(self.status_image)

        # Status Label
        self.status_label = Label(
            text="Tap the button to start",
            font_size='18sp',
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(self.status_label)

        # Start/Stop Button
        self.control_button = Button(
            text="Start Assistant",
            size_hint=(0.5, 0.1),
            pos_hint={'center_x': 0.5},
            background_color=(0.2, 0.6, 0.8, 1),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        self.control_button.bind(on_press=self.toggle_assistant)
        layout.add_widget(self.control_button)

        self.backend_thread = None
        self.tara_backend = None
        self.is_running = False

        # Mapping status from backend to UI elements
        self.status_map = {
            "listening": ("Listening...", "images/listening.png"),
            "processing": ("Processing...", "images/processing.png"),
            "active": ("Tara is Active!", "images/active.png"),
            "speaking": ("Speaking...", "images/speaking.png"),
        }

        return layout

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def toggle_assistant(self, instance):
        if not self.is_running:
            self.is_running = True
            self.control_button.text = "Stop Assistant"
            self.status_label.text = "Initializing..."

            self.tara_backend = backend.TaraBackend(self.update_status_from_backend)
            self.backend_thread = threading.Thread(target=self.tara_backend.start)
            self.backend_thread.daemon = True
            self.backend_thread.start()
        else:
            self.is_running = False
            self.control_button.text = "Start Assistant"
            if self.tara_backend:
                self.tara_backend.stop()
            if self.backend_thread:
                self.backend_thread.join(timeout=1)
            self.tara_backend = None
            self.backend_thread = None
            self.status_label.text = "Assistant stopped. Tap to start."
            self.status_image.source = 'images/listening.png'

    def update_status_from_backend(self, message, status_key):
        Clock.schedule_once(lambda dt: self._update_ui(message, status_key))

    def _update_ui(self, message, status_key):
        if not self.is_running:
            return

        self.status_label.text = message

        default_message, default_image = self.status_map.get("listening")
        image_path = self.status_map.get(status_key, (None, default_image))[1]

        if os.path.exists(image_path):
            self.status_image.source = image_path
        else:
            self.status_image.source = default_image

    def on_stop(self):
        if self.tara_backend:
            self.tara_backend.stop()
        if self.backend_thread:
            self.backend_thread.join(timeout=1)

if __name__ == '__main__':
    TaraApp().run()