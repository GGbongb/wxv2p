from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt

class ExportOptionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加上方空白
        main_layout.addStretch(1)
        
        # 创建中间的按钮布局
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(20)  # 设置按钮之间的间距
        
        # 创建两个主要功能按钮
        self.export_images_button = self.create_action_button("导出全部单个图片")
        self.export_pdf_button = self.create_action_button("整理为pdf")
        
        center_layout.addWidget(self.export_images_button)
        center_layout.addWidget(self.export_pdf_button)
        
        # 添加中间布局到主布局
        main_layout.addLayout(center_layout)
        
        # 添加底部空白
        main_layout.addStretch(1)
        
    def create_action_button(self, text):
        """创建统一样式的功能按钮"""
        button = QPushButton(text)
        button.setStyleSheet("""
            QPushButton {
                background-color: #999999;
                color: black;
                border: none;
                padding: 20px 40px;
                border-radius: 15px;
                font-size: 18px;
                min-width: 250px;
            }
            QPushButton:hover {
                background-color: #888888;
            }
        """)
        button.setFixedSize(300, 80)
        return button