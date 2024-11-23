from PyQt5.QtWidgets import QApplication
from components.video_drag_window import VideoDragDropWindow
import sys

def run(show_window=True):
    """运行应用程序"""
    app = QApplication(sys.argv)
    main_window = VideoDragDropWindow()
    
    if show_window:
        main_window.show()
        return app.exec_()
    else:
        app.main_window = main_window  # 保存主窗口引用
        return app



if __name__ == "__main__":
    run()