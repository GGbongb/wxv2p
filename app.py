import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
                             QPushButton, QFileDialog, QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QColor, QLinearGradient

class VideoDragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信聊天记录转图片工具")
        self.setGeometry(100, 100, 800, 600)

        # 设置主窗口背景渐变
        self.update_background()

        # 设置主窗口布局
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(50)  # 增加组件之间的间距
        
        # 拖放区域
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
        layout.addWidget(self.drop_area)

        # 添加按钮
        self.process_button = QPushButton("点击开始吧", self)
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
        layout.addWidget(self.process_button, alignment=Qt.AlignCenter)

        # 设置主窗口的中央小部件
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 启用拖放功能
        self.setAcceptDrops(True)

        # 存储视频路径
        self.video_path = None

    def update_background(self):
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(255, 200, 200))  # 更红的背景色
        gradient.setColorAt(1, QColor(255, 150, 150))
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setBrush(self.backgroundRole(), gradient)
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.video_path = urls[0].toLocalFile()
            self.drop_area.setText(f"文件加载成功:\n{self.video_path}")
            self.drop_area.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)

    def process_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先拖入视频文件！")
            return
        
        # 这里添加视频处理逻辑
        QMessageBox.information(self, "提示", "视频处理功能尚未实现")

def run():
    app = QApplication(sys.argv)
    window = VideoDragDropWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
