import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
                             QPushButton, QFileDialog, QMessageBox, QSizePolicy, QProgressBar,
                             QHBoxLayout, QScrollArea)
from PyQt5.QtCore import Qt, QMimeData, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QColor, QLinearGradient, QPixmap, QImage, QIcon

class FunProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFA500;
                border-radius: 15px;
                background-color: #FFFACD;
                text-align: center;
                color: #FF4500;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FF6347;
                border-radius: 13px;
            }
        """)
        self.setFixedHeight(30)
        self.setTextVisible(True)
        self.setFormat("%p%")

class VideoProcessThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(list)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = []
        last_frame = None

        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break

            if last_frame is None or self.frame_difference(last_frame, frame) > 0.1:
                frames.append(frame)
                last_frame = frame

            self.progress.emit(int((i + 1) / total_frames * 100))

        cap.release()
        self.finished.emit(frames)

    def frame_difference(self, frame1, frame2):
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        return np.mean(diff) / 255.0

class ImageViewer(QWidget):
    def __init__(self, images):
        super().__init__()
        self.images = images
        self.current_index = 0
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_button = QPushButton()
        self.next_button = QPushButton()
        self.prev_button.setIcon(QIcon("resources/left_arrow.png"))
        self.next_button.setIcon(QIcon("resources/right_arrow.png"))
        self.prev_button.setFixedSize(50, 50)
        self.next_button.setFixedSize(50, 50)
        self.prev_button.clicked.connect(self.show_previous)
        self.next_button.clicked.connect(self.show_next)
        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_button)
        layout.addLayout(nav_layout)

        # Delete button
        delete_layout = QHBoxLayout()
        self.delete_button = QPushButton("删除")
        self.delete_button.setFixedWidth(200)
        self.delete_button.clicked.connect(self.delete_current)
        delete_layout.addStretch()
        delete_layout.addWidget(self.delete_button)
        delete_layout.addStretch()
        layout.addLayout(delete_layout)

        self.setLayout(layout)
        self.show_image()

    def show_image(self):
        if self.images:
            pixmap = QPixmap.fromImage(self.images[self.current_index])
            self.image_label.setPixmap(pixmap.scaled(552, 1280, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def show_next(self):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_image()

    def delete_current(self):
        if self.images:
            del self.images[self.current_index]
            if self.current_index >= len(self.images):
                self.current_index = max(0, len(self.images) - 1)
            self.show_image()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Delete:
            self.delete_current()
        elif event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Right:
            self.show_next()

class VideoDragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信聊天记录转图片工具")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.init_drag_drop_ui()

        self.video_path = None

    def init_drag_drop_ui(self):
        self.drop_area = QLabel("拖曳微信录屏文件到此", self)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 36px;
                font-weight: bold;
            }
        """)
        self.drop_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.drop_area)

        self.process_button = QPushButton("开始截图", self)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
        """)
        self.process_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.process_button.clicked.connect(self.process_video)
        self.layout.addWidget(self.process_button, alignment=Qt.AlignCenter)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.video_path = urls[0].toLocalFile()
            self.drop_area.setText("文件已加载，点击开始截图")

    def process_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先拖入视频文件！")
            return

        # Clear the layout
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)

        self.progress_bar = FunProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)

        self.thread = VideoProcessThread(self.video_path)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.show_images)
        self.thread.start()

    def update_progress(self, value):
        self.animation.setStartValue(self.progress_bar.value())
        self.animation.setEndValue(value)
        self.animation.start()

    def show_images(self, frames):
        images = [QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped() for frame in frames]
        self.image_viewer = ImageViewer(images)
        self.setCentralWidget(self.image_viewer)

def run():
    app = QApplication(sys.argv)
    window = VideoDragDropWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
