from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window

Window.clearcolor = (0, 0.6, 0.1, 1.0)
Window.size = (800, 480)


class HomeScreen(Screen):
   pass


class OtherScreen(Screen):
   pass


class RootWidget(ScreenManager):
   pass


class MainApp(App):

   def build(self):
      self.title = "ALRI App"

      return RootWidget()

if __name__ == "__main__":
    MainApp().run()