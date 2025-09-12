from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.boxlayout import BoxLayout
from api_json_creator import *
from datetime import datetime, timedelta, timezone
import threading
import os
import json
from kivy.clock import Clock

class ButtonApp(App):
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.exam_updater = None  # reference to scheduled task
		self.prev_scores = {}
		self.last_update = {}
		self.load_counter = 0

	def build(self):
		self.layout = FloatLayout()
		self.show_ids = False  # default → show names

		# Categories to create
		self.categories = [
			{"name": "Campuses", "x": 0.005, "filename": "campuses.json"},
			{"name": "Cursus", "x": 0.225, "filename": "cursus.json"},
			{"name": "Exams", "x": 0.445, "filename": "exams.json"},
		]

		# Checkbox + Label
		activation_checkbox = CheckBox(
			size_hint=(0.05, 0.05),
			pos_hint={'x': 0.94, 'top': 0.99},
			active=False
		)
		activation_checkbox.bind(active=self.on_checkbox_toggle)

		activation_label = Label(
			text="Display ID instead of names?",
			font_size="15sp",
			size_hint=(0.2, 0.05),
			pos_hint={'x': 0.7325, 'top': 0.99},
			color=(1, 1, 1, 1)
		)

		self.layout.add_widget(activation_checkbox)
		self.layout.add_widget(activation_label)

		# rest of your buttons ...
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

			# Scrollable dropdown
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
			for other_name, other_scroll in self.scrollviews.items():
				if other_name != name:
					other_scroll.opacity = 0
					self.buttons[other_name].text = other_name
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
	
	def on_checkbox_toggle(self, instance, value):
		self.show_ids = value
		print(f"✅ Checkbox toggled → show_ids={self.show_ids}")

	def load_from_file(self, name, filename):
		try:
			with open(filename, "r", encoding="utf-8") as f:
				data = json.load(f)

			# Convert dict {name:id} → list of dicts
			if isinstance(data, dict):
				items = [{"name": k, "id": v} for k, v in data.items()]
			else:
				items = []

			# 🔑 Sort items if we're showing IDs
			if self.show_ids:
				items.sort(key=lambda x: x["id"])
			else:
				items.sort(key=lambda x: x["name"].lower())

			grid = self.grids[name]
			grid.clear_widgets()
			for item in items:
				# Show ID if checkbox is active, otherwise show name
				display_text = str(item["id"]) if self.show_ids else item["name"]

				btn = Button(
					text=display_text,
					size_hint_y=None,
					height=40
				)
				btn.campus_data = item
				btn.bind(on_press=lambda inst, n=name: self.on_item_selected(inst, n))
				grid.add_widget(btn)
		except Exception as e:
			print(f"❌ Error loading {filename}: {e}")

	def show_popup_message(self, title, message):
		popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
		label = Label(text=message, font_size="16sp")
		close_btn = Button(text="Close", size_hint=(1, 0.3))
		popup_content.add_widget(label)
		popup_content.add_widget(close_btn)

		popup = Popup(
			title=title,
			content=popup_content,
			size_hint=(0.6, 0.4),
			auto_dismiss=False
		)
		close_btn.bind(on_press=popup.dismiss)
		popup.open()

	def exam_tracker_grid(self, project_id, date_str):
		import requests
		from functools import partial
		import threading

		# Show loading popup
		Clock.schedule_once(lambda dt: self.show_loading_popup(), 0)

		def fetch_and_build():
			try:
				# Pick campus from GUI (fallback 62)
				if self.buttons["Campuses"].text != "Campuses":
					with open("campuses.json", "r") as f:
						campus_map = json.load(f)
					campus_id = campus_map.get(self.buttons["Campuses"].text, 62)
				else:
					campus_id = 62

				date_1 = f"{date_str}T01:00:00.205Z"
				date_2 = f"{date_str}T23:00:00.205Z"

				token = get_access_token()
				if not token:
					Clock.schedule_once(lambda dt: self.show_popup_message("❌ Error", "Unable to obtain access token."), 0)
					return

				headers = {"Authorization": f"Bearer {token}"}
				all_data = []
				page = 1
				per_page = 100

				# Fetch all pages
				while True:
					url = f"https://api.intra.42.fr/v2/projects/{project_id}/projects_users"
					params = {
						"filter[campus]": campus_id,
						"range[marked_at]": f"{date_1},{date_2}",
						"page[size]": per_page,
						"page[number]": page,
					}
					resp = requests.get(url, headers=headers, params=params)
					if resp.status_code != 200:
						Clock.schedule_once(lambda dt: self.show_popup_message("❌ Error",
							f"Failed to fetch page {page}: {resp.status_code}"), 0)
						return

					page_data = resp.json()
					if not page_data:
						break

					all_data.extend(page_data)
					page += 1
					time.sleep(0.2)

				if not all_data:
					Clock.schedule_once(lambda dt: self.show_popup_message("📭 Info", "Exam not accessible yet or no data."), 0)
					return

				# Sort by final_mark descending, then marked_at
				all_data.sort(key=lambda x: (-(x.get("final_mark") or -1), x.get("marked_at", "")))

				# Schedule GUI update on main thread
				Clock.schedule_once(lambda dt: self.build_exam_grid(all_data), 0)
			finally:
				# Close loading popup after done
				Clock.schedule_once(lambda dt: self.close_popup(None), 0)

		# Run fetching in a separate thread to avoid freezing GUI
		threading.Thread(target=fetch_and_build).start()


	def build_exam_grid(self, all_data):
		from functools import partial
		from dateutil import parser  # for parsing ISO timestamps

		self.load_counter += 1
		

		# Build GridLayout
		cols = 4
		rows = (len(all_data) + cols - 1) // cols
		grid = GridLayout(cols=cols, spacing=5, size_hint_y=None, padding=5)
		grid.bind(minimum_height=grid.setter('height'))

		# Fill columns
		columns = [[] for _ in range(cols)]
		for idx, entry in enumerate(all_data):
			col_idx = idx // rows
			columns[col_idx].append((idx + 1, entry))

		for row_idx in range(rows):
			for col in columns:
				if row_idx < len(col):
					rank, entry = col[row_idx]
					login = entry["user"]["login"]
					score = entry.get("final_mark", 0)
					status = entry.get("status", "unknown")
					time_marked_str = entry.get("marked_at", None)
					prefix = str(rank)

					now = datetime.now(timezone.utc)
					time_marked_str = entry.get("marked_at")  # returns None if missing

					if time_marked_str:
						time_marked = parser.isoparse(time_marked_str)
						delta_seconds = (now - time_marked).total_seconds()
					else:
						delta_seconds = None  # or some default

					# Update previous score
					if login not in self.prev_scores or self.prev_scores[login] != score:
						self.prev_scores[login] = score
						self.last_update[login] = time_marked

					# Determine color
					if status == "finished":
						color = hex_to_rgba("#98fb98")  # green
					elif (now - self.last_update.get(login, now)).total_seconds() > 3600:  # 30min
						color = hex_to_rgba("#ff4c4c")  # red if unchanged >30min
					elif (now - self.last_update.get(login, now)).total_seconds() < 300:  # 5min
						color = hex_to_rgba("#00b7eb")  # blue if score changed
					else:
						color = hex_to_rgba("#b0b0b0")  # gray otherwise

					text = f"{prefix} {login} {score}"
					btn = Button(
						text=text,
						size_hint_y=None,
						height=25,
						font_size="18sp",
						background_color=(0.2, 0.6, 0.8, 1),
						color=color
					)
					btn.bind(on_press=partial(self.open_user_profile, login))
					grid.add_widget(btn)
				else:
					grid.add_widget(Label(text="", size_hint_y=None, height=25))

		# Remove previous scrollview if exists
		if hasattr(self, "scrollview_exam"):
			self.layout.remove_widget(self.scrollview_exam)

		scrollview = ScrollView(size_hint=(0.95, 0.85), pos_hint={'x': 0.025, 'y': 0.05})
		scrollview.add_widget(grid)
		self.layout.add_widget(scrollview)
		self.scrollview_exam = scrollview

	def open_user_profile(self, login, *args):
		# Example: open intra 42 profile in browser
		import webbrowser
		url = f"https://profile.intra.42.fr/users/{login}"
		webbrowser.open(url)

	def on_item_selected(self, instance, category_name):
		data = instance.campus_data
		display_text = str(data["id"]) if self.show_ids else data["name"]
		self.buttons[category_name].text = display_text
		self.scrollviews[category_name].opacity = 0
		print(f"✅ Selected {category_name}: {data['name']} (id={data['id']})")

		# Cancel previous scheduled exam updates
		if self.exam_updater:
			Clock.unschedule(self.exam_updater)
			self.exam_updater = None

		if category_name == "Exams":
			# Default to today
			today = datetime.today().strftime("%Y-%m-%d")
			
			# Call exam tracker immediately
			self.exam_tracker_grid(data["id"], today)

			# Schedule repeated update every 15 seconds
			self.exam_updater = Clock.schedule_interval(
				lambda dt: self.exam_tracker_grid(data["id"], today),
				15
			)
		else:
			# Not an exam → ensure updater is stopped
			if self.exam_updater:
				Clock.unschedule(self.exam_updater)
				self.exam_updater = None

	def close_popup(self, dt):
		if hasattr(self, "popup") and self.popup:
			self.popup.dismiss()
			print("✅ Done loading.")

def hex_to_rgba(hex_color, alpha=1):
	hex_color = hex_color[1:]
	r = int(hex_color[0:2], 16) / 255
	g = int(hex_color[2:4], 16) / 255
	b = int(hex_color[4:6], 16) / 255
	return (r, g, b, alpha)

if __name__ == '__main__':
	ButtonApp().run()
