from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor
import logging
from tools.utils import resource_path

# 配置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImageViewer(QWidget):
    processed_images = []
    switch_to_export_page = pyqtSignal()
    
    def __init__(self, frames):
        super().__init__()
        logger.debug("初始化 ImageViewer")
        self.images = [QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped() for frame in frames]
        ImageViewer.processed_images = self.images  # 初始化存储
        self.current_index = 0
        self.selected_image = 0  # 0 表示左侧图片被选中，1 表示右侧图片被选中
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: #FFF0E0;")  # 暖色背景
        self.setFixedSize(1920, 1500)  # 与 video_drag_window 保持一致的大小

        main_layout = QHBoxLayout()
        
        # 左侧布局（箭头 + 按钮）
        left_layout = QVBoxLayout()
        left_layout.addStretch(1)  # 添加弹性空间将箭头推到中间

        self.prev_button = QPushButton()
        self.prev_button.setIcon(QIcon("resources/left_arrow.png"))
        self.prev_button.setIconSize(QSize(50, 50))
        self.prev_button.setStyleSheet("background: transparent;")
        self.prev_button.clicked.connect(self.show_previous)
        left_layout.addWidget(self.prev_button, alignment=Qt.AlignCenter)
        
        left_layout.addStretch(1)  # 添加弹性空间将箭头推到中间
        
        self.delete_button = self.create_vertical_button("空格\n删除", "#F1C40F")
        self.delete_button.clicked.connect(self.delete_current)
        left_layout.addWidget(self.delete_button, alignment=Qt.AlignBottom)
        
        main_layout.addLayout(left_layout)

        # 图片显示区域
        image_area_layout = QVBoxLayout()
        self.image_frame = QFrame()
        self.image_frame.setStyleSheet("background-color: white;")
        self.image_layout = QHBoxLayout(self.image_frame)
        self.image_labels = [QLabel() for _ in range(2)]
        for label in self.image_labels:
            label.setAlignment(Qt.AlignCenter)
            self.image_layout.addWidget(label)
        image_area_layout.addWidget(self.image_frame, 1)  # 图片区域占据剩余空间

        # 添加图片序号标签
        self.image_count_label = QLabel()
        self.image_count_label.setAlignment(Qt.AlignCenter)
        self.image_count_label.setStyleSheet("color: #2c3e50; font-size: 18px; font-weight: bold;")
        image_area_layout.addWidget(self.image_count_label)

        main_layout.addLayout(image_area_layout, 1)

        # 添加选择框
        self.selection_frame = QFrame(self.image_frame)
        self.selection_frame.setStyleSheet("border: 3px solid #E74C3C; border-radius: 10px; background: transparent;")
        self.selection_frame.hide()  # 初始时隐藏选择框

        # 右侧布局（箭头 + 按钮）
        right_layout = QVBoxLayout()
        right_layout.addStretch(1)  # 添加弹性空间将箭头推到中间

        self.next_button = QPushButton()
        self.next_button.setIcon(QIcon("resources/right_arrow.png"))
        self.next_button.setIconSize(QSize(50, 50))
        self.next_button.setStyleSheet("background: transparent;")
        self.next_button.clicked.connect(self.show_next)
        right_layout.addWidget(self.next_button, alignment=Qt.AlignCenter)
        
        right_layout.addStretch(1)  # 添加弹性空间将箭头推到中间
        
        self.next_step_button = self.create_vertical_button("下一步", "#F1C40F")
        self.next_step_button.clicked.connect(self.go_to_next_step)
        right_layout.addWidget(self.next_step_button, alignment=Qt.AlignBottom)
        
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)
        self.show_images()
        self.setFocusPolicy(Qt.StrongFocus)

        # 使用 QTimer 延迟更新选择框位置
        QTimer.singleShot(100, self.update_selection_frame)

    def update_image_count_label(self):
            current_image = self.current_index + self.selected_image + 1
            total_images = len(self.images)
            self.image_count_label.setText(f"第 {current_image} 张 / 共计 {total_images} 张")

    def create_vertical_button(self, text, color):
        button = QPushButton("\n".join(text))
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 25px;
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
            self.update_image_count_label()

    def update_selection_frame(self):
        if self.images:
            selected_label = self.image_labels[self.selected_image]
            self.selection_frame.setGeometry(selected_label.geometry())
            self.selection_frame.show()  # 显示选择框
        else:
            self.selection_frame.hide()  # 如果没有图片，隐藏选择框

    def show_previous(self):
        if self.selected_image == 1:
            self.selected_image = 0
        elif self.current_index > 0:
            self.current_index -= 1
        self.show_images()
        self.update_selection_frame()
        self.update_image_count_label()

    def show_next(self):
        if self.selected_image == 0 and self.current_index + 1 < len(self.images):
            self.selected_image = 1
        elif self.current_index + 2 < len(self.images):
            self.current_index += 1
            self.selected_image = 0
        self.show_images()
        self.update_selection_frame()
        self.update_image_count_label()

    def delete_current(self):
        if self.images:
            del self.images[self.current_index + self.selected_image]
            ImageViewer.processed_images = self.images  # 更新存储的图片
            if self.current_index + self.selected_image >= len(self.images):
                self.current_index = max(0, len(self.images) - 2)
                self.selected_image = 0
            self.show_images()
            self.update_selection_frame()
            self.update_image_count_label()
            
    def go_to_next_step(self):
        logger.debug("点击下一步按钮")
        try:
            # 发出切换页面的信号
            self.switch_to_export_page.emit()
            logger.debug("发出切换页面信号")
        except Exception as e:
            logger.error(f"切换页面时发生错误: {str(e)}", exc_info=True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space or event.key() == Qt.Key_Delete:
            self.delete_current()
        elif event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Right:
            self.show_next()