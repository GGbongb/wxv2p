from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
import os
from datetime import datetime
from .pdf_generator import PDFGenerator

class ExportOptionsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 设置整个窗口的背景色
        self.setStyleSheet("background-color: #FFF5E6;")  # 更浅的暖色调背景
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # 创建顶部布局（用于放置返回按钮）
        top_layout = QHBoxLayout()
        top_layout.setAlignment(Qt.AlignRight)
        
        # 创建返回主页按钮
        self.home_button = QPushButton()
        self.home_button.setIcon(QIcon("resources/home.png"))
        self.home_button.setIconSize(QSize(24, 24))
        self.home_button.setText("返回主页")
        self.home_button.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
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
        
        # 连接按钮信号到槽函数
        self.export_images_button.findChild(QPushButton).clicked.connect(self.export_images)
        self.export_pdf_button.findChild(QPushButton).clicked.connect(self.export_pdf)
        
    def create_action_button(self, text, color, description=""):
        """创建带有描述文本的功能按钮"""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        
        # 如果有描述文本，先添加描述
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
        
        # 创建按钮
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

    def export_images(self):
        """导出所有图片到选择的文件夹"""
        print("导出图片方法被调用")  # 添加这行用于测试
        from components.image_viewer import ImageViewer
        
        if not ImageViewer.processed_images:
            QMessageBox.warning(self, "警告", "没有可导出的图片！")
            return
            
        # 获取用户选择的保存目录
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择保存目录",
            os.path.expanduser("~/Desktop"),  # 默认打开桌面
            QFileDialog.ShowDirsOnly
        )
        
        if not folder_path:  # 用户取消选择
            return
            
        try:
            # 创建以当前时间命名的子文件夹
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = os.path.join(folder_path, f"微信聊天记录_{timestamp}")
            os.makedirs(export_folder, exist_ok=True)
            
            # 导出所有图片
            total = len(ImageViewer.processed_images)
            for i, image in enumerate(ImageViewer.processed_images):
                # 生成文件名
                filename = f"聊天记录_{i+1:03d}.png"
                filepath = os.path.join(export_folder, filename)
                
                # 保存图片
                image.save(filepath, "PNG")
            
            # 显示成功消息
            QMessageBox.information(
                self,
                "导出成功",
                f"已成功导出 {total} 张图片到:\n{export_folder}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "导出失败",
                f"导出过程中发生错误：\n{str(e)}"
            )

    def export_pdf(self):
        """处理PDF导出按钮点击"""
        from components.pricing_plan_page import PricingPlanPage
        
        # 显示价格方案页面
        pricing_page = PricingPlanPage(self)
        self.parent().setCentralWidget(pricing_page)