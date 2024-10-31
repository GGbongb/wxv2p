from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

class ExportOptionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 设置背景色
        self.setStyleSheet("background-color: #FFF0E0;")  # 暖色调背景
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 创建顶部布局（用于放置返回按钮）
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignRight)
        
        # 创建返回主页按钮
        self.home_button = QPushButton()
        self.home_button.setIcon(QIcon("resources/home.png"))  # 需要准备home图标
        self.home_button.setIconSize(QSize(24, 24))
        self.home_button.setText("返回主页")
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2c3e50;
                border: 2px solid #2c3e50;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
                color: white;
            }
        """)
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.clicked.connect(self.go_to_home)
        top_layout.addWidget(self.home_button)
        
        main_layout.addLayout(top_layout)
        
        # 添加标题
        title_label = QLabel("选择导出方式")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 48px;
                font-weight: bold;
                margin: 40px 0;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 添加上方空白
        main_layout.addStretch(1)
        
        # 创建中间的按钮布局
        center_layout = QVBoxLayout()
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(40)  # 增加按钮之间的间距
        
        # 创建两个主要功能按钮
        self.export_images_button = self.create_action_button(
            "导出全部单个图片",
            "#3498db",  # 蓝色
            "将所有图片分别保存为独立文件"
        )
        self.export_pdf_button = self.create_action_button(
            "整理为PDF文档",
            "#e74c3c",  # 红色
            "将所有图片合并为单个PDF文件"
        )
        
        center_layout.addWidget(self.export_images_button)
        center_layout.addWidget(self.export_pdf_button)
        
        # 添加中间布局到主布局
        main_layout.addLayout(center_layout)
        
        # 添加底部空白
        main_layout.addStretch(1)
        
    def create_action_button(self, text, color, description=""):
        """创建带有描述文本的功能按钮"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 25px 50px;
                border-radius: 20px;
                font-size: 28px;
                font-weight: bold;
                min-width: 400px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """)
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedSize(450, 100)
        
        # 添加描述文本
        if description:
            desc_label = QLabel(description)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 16px;
                }
            """)
            layout.addWidget(desc_label)
        
        layout.addWidget(button)
        return container

    def darken_color(self, color):
        """返回稍深的颜色用于悬停效果"""
        from PyQt5.QtGui import QColor
        c = QColor(color)
        h, s, v, _ = c.getHsv()
        return QColor.fromHsv(h, s, int(v * 0.8)).name()

    def go_to_home(self):
        """返回主页的方法"""
        from components.video_drag_window import VideoDragDropWindow
        main_window = VideoDragDropWindow()
        self.parent().setCentralWidget(main_window)