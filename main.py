from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from api_json_creator import *
import threading
import os
import json

class ButtonApp(App):
	def build(self):
		self.layout = FloatLayout()

		# Categories to create
		self.categories = [
			{"name": "Campuses", "x": 0.005, "filename": "campuses.json"},
			{"name": "Cursus", "x": 0.225, "filename": "cursus.json"},
			{"name": "Exams", "x": 0.445, "filename": "exams.json"},
		]

		self.buttons = {}
		self.reload_buttons = {}
		self.scrollviews = {}
		self.grids = {}

		for cat in self.categories:
			name = cat["name"]
			x_pos = cat["x"]
			filename = cat["filename"]

			# Main button
			btn = Button(
				text=name,
				font_size="15sp",
				background_color=(0.2, 0.6, 0.8, 1),
				color=(1, 1, 1, 1),
				size_hint=(0.15, 0.05),
				pos_hint={'x': x_pos, 'top': 0.99}
			)
			self.layout.add_widget(btn)
			self.buttons[name] = btn

			# Reload button
			reload_btn = Button(
				text="🔁",
				font_size="15sp",
				font_name="fonts/NotoEmoji-Regular.ttf",
				background_color=(0.2, 0.6, 0.8, 1),
				color=(1, 1, 1, 1),
				size_hint=(0.05, 0.05),
				pos_hint={'x': x_pos + 0.15, 'top': 0.99}
			)
			self.layout.add_widget(reload_btn)
			self.reload_buttons[name] = reload_btn

			# Scrollable dropdown (hidden at start)
			scrollview = ScrollView(
				size_hint=(0.25, 0.4),
				pos_hint={'x': x_pos, 'top': 0.935},
				do_scroll_x=False,
				do_scroll_y=True
			)
			grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
			grid.bind(minimum_height=grid.setter("height"))
			scrollview.add_widget(grid)
			scrollview.opacity = 0
			self.layout.add_widget(scrollview)

			self.scrollviews[name] = scrollview
			self.grids[name] = grid

			# Bind events
			btn.bind(on_press=lambda inst, n=name, f=filename: self.toggle_list(n, f))
			reload_btn.bind(on_press=lambda inst, n=name, f=filename: self.on_reload(n, f))

		return self.layout

	def toggle_list(self, name, filename):
		scrollview = self.scrollviews[name]
		btn = self.buttons[name]

		if scrollview.opacity == 0:
			self.load_or_generate(name, filename)
			scrollview.opacity = 1
			btn.text = name
		else:
			scrollview.opacity = 0
			btn.text = name

	def on_reload(self, name, filename):
		if os.path.exists(filename):
			os.remove(filename)
		self.show_loading_popup()
		threading.Thread(target=self.run_heavy_task, args=(name, filename)).start()

	def show_loading_popup(self):
		loading_label = Label(text="Loading...", font_size="18sp")
		self.popup = Popup(
			title='Please wait',
			content=loading_label,
			size_hint=(0.4, 0.2),
			auto_dismiss=False
		)
		self.popup.open()

	def run_heavy_task(self, name, filename):
		token = get_access_token()

		try:
			if name == "Campuses":
				data = get_all(token)  # your current get_all already gets campuses
			elif name == "Cursus":
				data = get_all(token, "https://api.intra.42.fr/v2/cursus")  # you need a function that fetches /v2/cursus
			elif name == "Exams":
				# For exams, we need campus_id and cursus_id
				# You can pick defaults or store selected ones
				if self.buttons["Campuses"].text != "Campuses":
					campus_name = self.buttons["Campuses"].text
					with open("campuses.json", "r") as f:
						campus_map = json.load(f)
					campus_id = campus_map.get(campus_name)
				else:
					campus_id = 62 # Default to Le Havre
				if self.buttons["Cursus"].text != "Cursus":
					cursus_name = self.buttons["Cursus"].text
					with open("cursus.json", "r") as f:
						cursus_map = json.load(f)
					cursus_id = cursus_map.get(cursus_name)
				else:
					cursus_id = 9 # Default to C Piscine
				data = get_all(token, f"https://api.intra.42.fr/v2/campus/{campus_id}/cursus/{cursus_id}/exams")
			else:
				data = []

			save_ids_to_json(data, filename)
			Clock.schedule_once(lambda dt: self.on_data_ready(name, filename), 0)
		except Exception as e:
			print(f"❌ Error fetching {name}: {e}")
			Clock.schedule_once(lambda dt: self.close_popup(None), 0)

	def load_or_generate(self, name, filename):
		if not os.path.exists(filename):
			self.show_loading_popup()
			threading.Thread(target=self.run_heavy_task, args=(name, filename)).start()
		else:
			self.load_from_file(name, filename)

	def on_data_ready(self, name, filename):
		self.close_popup(None)
		self.load_from_file(name, filename)

	def load_from_file(self, name, filename):
		try:
			with open(filename, "r", encoding="utf-8") as f:
				data = json.load(f)
			# Convert dict {name:id} → list of dicts
			if isinstance(data, dict):
				items = [{"name": k, "id": v} for k, v in data.items()]
			else:
				items = []

			grid = self.grids[name]
			grid.clear_widgets()
			for item in items:
				btn = Button(
					text=item["name"],
					size_hint_y=None,
					height=40
				)
				btn.campus_data = item
				btn.bind(on_press=lambda inst, n=name: self.on_item_selected(inst, n))
				grid.add_widget(btn)
		except Exception as e:
			print(f"❌ Error loading {filename}: {e}")

	def on_item_selected(self, instance, category_name):
		data = instance.campus_data
		self.buttons[category_name].text = data["name"]
		self.scrollviews[category_name].opacity = 0
		print(f"✅ Selected {category_name}: {data['name']} (id={data['id']})")

	def close_popup(self, dt):
		if hasattr(self, "popup") and self.popup:
			self.popup.dismiss()
			print("✅ Done loading.")


if __name__ == '__main__':
	ButtonApp().run()
