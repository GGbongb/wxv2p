from PyQt5.QtWidgets import QApplication
from components.video_drag_window import VideoDragDropWindow
import sys

class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = VideoDragDropWindow()

def run(show_window=True):
    """运行应用程序"""
    app_instance = App()
    if show_window:
        app_instance.main_window.show()
    return app_instance  # 返回 App 实例


if __name__ == "__main__":
    run()