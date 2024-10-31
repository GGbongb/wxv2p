from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget,
                             QPushButton, QMessageBox, QSizePolicy, QTextEdit)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from .fun_progress_bar import FunProgressBar
from .video_process_thread import VideoProcessThread
from .image_viewer import ImageViewer
from components.video_process_thread import VideoProcessThread

class VideoDragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信聊天记录转图片工具")
        self.setGeometry(100, 100, 1920,1500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.init_drag_drop_ui()

        self.video_path = None

    def init_drag_drop_ui(self):
        # 创建一个容器用于文字显示
        self.text_container = QWidget()
        text_layout = QVBoxLayout(self.text_container)
        
        # 添加上方空白
        text_layout.addStretch(4)
        
        # 拖放文字标签
        self.drop_area = QLabel("拖曳微信录屏文件到此", self)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 72px;
                font-weight: bold;
            }
        """)
        text_layout.addWidget(self.drop_area)
        
        # 添加文字和按钮之间的空白
        text_layout.addStretch(3)
        
        # 开始按钮
        self.process_button = QPushButton("开始截图", self)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: white;
                border: none;
                padding: 30px 60px;
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
        self.process_button.hide()  # 初始时隐藏按钮
        text_layout.addWidget(self.process_button, alignment=Qt.AlignCenter)
        
        # 添加底部空白
        text_layout.addStretch(4)
        
        # 将容器添加到主布局
        self.layout.addWidget(self.text_container)
        
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
            self.process_button.show()  # 显示开始按钮

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
        
        # 添加日志显示功能
       # self.log_display = QTextEdit(self)
       # self.log_display.setReadOnly(True)
       # self.layout.addWidget(self.log_display)

        # def display_log(message):
        #     self.log_display.append(message)

        # self.thread.log_message.connect(display_log)
        
        self.thread.start()

    def update_progress(self, value):
        self.animation.setStartValue(self.progress_bar.value())
        self.animation.setEndValue(value)
        self.animation.start()

    def show_images(self, frames):
        self.image_viewer = ImageViewer(frames)
        self.setCentralWidget(self.image_viewer)