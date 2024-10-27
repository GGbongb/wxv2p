from PyQt5.QtWidgets import QApplication
from components.video_drag_window import VideoDragDropWindow

def run():
    app = QApplication([])
    window = VideoDragDropWindow()
    window.show()
    app.exec_()



if __name__ == "__main__":
    run()