from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QLineEdit)
from PyQt5.QtCore import Qt
from .activation_manager import ActivationManager
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap
import logging
import os

logger = logging.getLogger(__name__)

class PricingPlanPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activation_manager = ActivationManager()
        self.init_ui()
        
    def init_ui(self):
        # 设置背景色
        self.setStyleSheet("background-color: #f5f6fa;")
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)  # 增加页面边距
        main_layout.setSpacing(40)  # 增加组件间距
        
        # 添加顶部空白
        main_layout.addStretch(1)
        
        # 创建水平布局用于放置文字和二维码
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        # 左侧文字描述
        text_layout = QVBoxLayout()
        text_layout.setAlignment(Qt.AlignLeft)  # 左对齐
        
        title = QLabel("购买本软件")
        title.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        text_layout.addWidget(title, alignment=Qt.AlignLeft)
        
        price_label = QLabel("价格：10元")
        price_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #27ae60;  /* 使用绿色 */
            }
        """)
        text_layout.addWidget(price_label, alignment=Qt.AlignLeft)
        
        features_label = QLabel("功能：无限导出PDF，一次付费永久使用")
        features_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #34495e;  /* 深灰色 */
            }
        """)
        text_layout.addWidget(features_label, alignment=Qt.AlignLeft)
        
        info_layout.addLayout(text_layout)  # 将文字布局添加到水平布局
        
        # 右侧二维码图片
        qr_code_label = QLabel()
        qr_code_path = os.path.join("resources", "qrcode.png")  # 使用资源目录中的二维码路径
        qr_code_pixmap = QPixmap(qr_code_path)  # 加载二维码图片
        qr_code_label.setPixmap(qr_code_pixmap.scaled(150, 150, Qt.KeepAspectRatio))  # 调整二维码大小
        qr_code_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(qr_code_label, alignment=Qt.AlignRight)  # 将二维码添加到右侧
        
        main_layout.addLayout(info_layout)  # 将信息布局添加到主布局
        
        # 添加分隔空间
        main_layout.addSpacing(40)
        
        # 添加激活码区域
        activation_container = QFrame()
        activation_container.setObjectName("activationContainer")
        activation_container.setStyleSheet("""
            QFrame#activationContainer {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 100px;
            }
        """)
        
        activation_layout = QVBoxLayout(activation_container)
        
        # 添加激活码提示
        activation_title = QLabel("购买后请输入激活码")
        activation_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 10px;
            }
        """)
        activation_title.setAlignment(Qt.AlignCenter)
        activation_layout.addWidget(activation_title)
        
        # 创建输入区域容器
        input_container = QHBoxLayout()
        input_container.setSpacing(15)
        input_container.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        # 添加激活码输入框
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("请输入激活码")
        self.activation_input.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                min-width: 300px;  /* 设置合适的宽度 */
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        input_container.addWidget(self.activation_input)
        
        # 添加激活按钮
        activate_button = QPushButton("激活")
        activate_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                border: none;
                border-radius: 8px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        activate_button.clicked.connect(self.verify_activation_code)
        input_container.addWidget(activate_button)
        
        activation_layout.addLayout(input_container)
        
        main_layout.addWidget(activation_container)
        
        # 添加底部空白
        main_layout.addStretch(1)

    def verify_activation_code(self):
        """验证激活码"""
        logger.debug("开始验证激活码")
        activation_code = self.activation_input.text().strip()
        if not activation_code:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return
        
        # 验证激活码
        success, message = self.activation_manager.activate(activation_code)
        
        if success:
            logger.debug("激活成功，准备返回导出页面")
            QMessageBox.information(self, "成功", message)
            
            try:
                # 返回导出页面
                from components.export_options_page import ExportOptionsPage
                export_page = ExportOptionsPage(self.parent())
                self.parent().setCentralWidget(export_page)
                # 自动开始导出
                export_page.generate_pdf()
                logger.debug("成功返回导出页面并开始生成PDF")
            except Exception as e:
                logger.error(f"返回导出页面时发生错误: {str(e)}", exc_info=True)
        else:
            QMessageBox.warning(self, "错误", message)
    
    def proceed_with_export(self):
        """继续导出操作"""
        from components.export_options_page import ExportOptionsPage
        export_page = ExportOptionsPage(self.parent())
        self.parent().setCentralWidget(export_page)
        # 触发PDF导出
        export_page.generate_pdf()