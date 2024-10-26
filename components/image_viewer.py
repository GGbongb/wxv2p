from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage, QIcon

class ImageViewer(QWidget):
    def __init__(self, frames):
        super().__init__()
        self.images = [QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped() for frame in frames]
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