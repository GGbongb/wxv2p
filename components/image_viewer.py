from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon,QColor 

class ImageViewer(QWidget):
    def __init__(self, frames):
        super().__init__()
        self.images = [QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped() for frame in frames]
        self.current_index = 0
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: #FFF0E0;")  # 暖色背景
        self.setFixedSize(1920,1500)  # 与 video_drag_window 保持一致的大小

        main_layout = QHBoxLayout()
        
        # 左侧布局（箭头 + 按钮）
        left_layout = QVBoxLayout()
        self.prev_button = QPushButton()
        self.prev_button.setIcon(QIcon("resources/left_arrow.png"))
        self.prev_button.setIconSize(QSize(50, 50))
        self.prev_button.setStyleSheet("background: transparent;")
        self.prev_button.clicked.connect(self.show_previous)
        left_layout.addWidget(self.prev_button, alignment=Qt.AlignCenter)
        
        self.delete_button = self.create_vertical_button("空格\n删除", "#F1C40F")
        self.delete_button.clicked.connect(self.delete_current)
        left_layout.addWidget(self.delete_button, alignment=Qt.AlignBottom)
        
        main_layout.addLayout(left_layout)

        # 图片显示区域
        self.image_frame = QFrame()
        self.image_frame.setStyleSheet("background-color: white;")
        self.image_layout = QHBoxLayout(self.image_frame)
        self.image_labels = [QLabel() for _ in range(2)]
        for label in self.image_labels:
            label.setAlignment(Qt.AlignCenter)
            self.image_layout.addWidget(label)
        main_layout.addWidget(self.image_frame, 1)  # 图片区域占据剩余空间

        # 右侧布局（箭头 + 按钮）
        right_layout = QVBoxLayout()
        self.next_button = QPushButton()
        self.next_button.setIcon(QIcon("resources/right_arrow.png"))
        self.next_button.setIconSize(QSize(50, 50))
        self.next_button.setStyleSheet("background: transparent;")
        self.next_button.clicked.connect(self.show_next)
        right_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)
        
        self.next_step_button = self.create_vertical_button("下一步", "#F1C40F")
        self.next_step_button.clicked.connect(self.go_to_next_step)
        right_layout.addWidget(self.next_step_button, alignment=Qt.AlignBottom)
        
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)
        self.show_images()

    def create_vertical_button(self, text, color):
        button = QPushButton("\n".join(text))
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        button.setFixedSize(80, 200)
        return button

    def darken_color(self, color):
        c = QColor(color)
        h, s, v, _ = c.getHsv()
        return QColor.fromHsv(h, s, max(0, v - 20)).name()

    def show_images(self):
        image_width = 552
        image_height = 1280
        for i, label in enumerate(self.image_labels):
            index = self.current_index + i
            if index < len(self.images):
                pixmap = QPixmap.fromImage(self.images[index])
                scaled_pixmap = pixmap.scaled(image_width, image_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                label.setPixmap(scaled_pixmap)
            else:
                label.clear()
        self.update_selection_frame()

    def update_selection_frame(self):
        for i, label in enumerate(self.image_labels):
            if i == 0:  # 只为左侧图片添加边框
                label.setStyleSheet("border: 3px solid #E74C3C; border-radius: 10px;")
            else:
                label.setStyleSheet("")

    def show_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_images()

    def show_next(self):
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.show_images()

    def delete_current(self):
        if self.images:
            del self.images[self.current_index]
            if self.current_index >= len(self.images):
                self.current_index = max(0, len(self.images) - 1)
            self.show_images()

    def go_to_next_step(self):
        print("进入下一步")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Delete:
            self.delete_current()
        elif event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Right:
            self.show_next()