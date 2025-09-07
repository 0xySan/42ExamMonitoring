from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from api_json_creator import *
import threading
import time


class ButtonApp(App):
	def build(self):
		self.layout = FloatLayout()

		self.btn = Button(
			text="Reload",
			font_size="15sp",
			background_color=(0.2, 0.6, 0.8, 1),
			color=(1, 1, 1, 1),
			size_hint=(0.1, 0.05),
			pos_hint={'x': 0.005, 'top': 0.99}
		)
		self.btn.bind(on_press=self.on_button_press)

		self.layout.add_widget(self.btn)
		return self.layout

	def on_button_press(self, instance):
		# Show loading popup
		self.show_loading_popup()

		# Run your long task in a background thread
		threading.Thread(target=self.run_heavy_task).start()

	def show_loading_popup(self):
		loading_label = Label(text="Loading...", font_size="18sp")
		self.popup = Popup(
			title='Please wait',
			content=loading_label,
			size_hint=(0.4, 0.2),
			auto_dismiss=False
		)
		self.popup.open()

	def run_heavy_task(self):
		token = get_access_token()
		campus = get_all(token)
		save_ids_to_json(campus)
		Clock.schedule_once(self.close_popup, 0)

	def close_popup(self, dt):
		if self.popup:
			self.popup.dismiss()
			print("✅ Done loading.")


if __name__ == '__main__':
	ButtonApp().run()
