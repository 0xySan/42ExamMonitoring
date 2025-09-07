from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.uix.togglebutton import ToggleButton
# Set the window to fullscreen
# Window.fullscreen = True  # You can also use 'auto' for dynamic behavior

class ButtonApp(App):

	def build(self):
		layout = FloatLayout()

		btn = Button(
			text="Push Me!",
			font_size="15sp",
			background_color=(0.2, 0.6, 0.8, 1),  # light blue
			color=(1, 1, 1, 1),  # white text
			size_hint=(0.1, 0.05),  # 15% width, 10% height
			pos_hint={'x': 0.005, 'top': 0.99}  # top-left corner
		)

		btn.bind(on_press=self.callback)
		layout.add_widget(btn)
		return layout

	def callback(self, instance):
		print('Yoooo !!!!!!!!!!!')

# Run the app
if __name__ == '__main__':
	ButtonApp().run()
