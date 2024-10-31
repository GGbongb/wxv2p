from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QLineEdit)
from PyQt5.QtCore import Qt
from .activation_manager import ActivationManager
from PyQt5.QtWidgets import QMessageBox
import logging

logger = logging.getLogger(__name__)

class PricingCard(QFrame):
    """价格卡片组件"""
    def __init__(self, title, price, duration, features):
        super().__init__()
        self.setObjectName("pricingCard")
        self.init_ui(title, price, duration, features)
        
    def init_ui(self, title, price, duration, features):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)  # 增加组件间距
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # 价格
        price_label = QLabel(f"¥{price}")
        price_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #e74c3c;
            }
        """)
        layout.addWidget(price_label, alignment=Qt.AlignCenter)
        
        # 时长
        duration_label = QLabel(duration)
        duration_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(duration_label, alignment=Qt.AlignCenter)
        
        # 特点列表
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    font-size: 20px;
                    color: #34495e;
                }
            """)
            layout.addWidget(feature_label, alignment=Qt.AlignCenter)
        
        # 设置卡片样式
        self.setStyleSheet("""
            QFrame#pricingCard {
                background-color: white;
                border-radius: 20px;
                padding: 40px;
                margin: 20px;
                min-width: 350px;
                min-height: 500px;
            }
            QFrame#pricingCard:hover {
                border: 2px solid #3498db;
            }
        """)

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
        
        # 添加标题
        title = QLabel("选择您的计划")
        title.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 40px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 创建卡片容器
        cards_layout = QHBoxLayout()
        cards_layout.setAlignment(Qt.AlignCenter)
        cards_layout.setSpacing(30)  # 增加卡片间距
        
        # 添加三个价格卡片
        monthly_features = ["无限导出PDF", "基础客服支持", "自动更新"]
        semi_annual_features = ["无限导出PDF", "优先客服支持", "自动更新", "更优惠的价格"]
        permanent_features = ["无限导出PDF", "VIP客服支持", "自动更新", "一次付费永久使用"]
        
        monthly_card = PricingCard("月付", "9.9", "每月", monthly_features)
        semi_card = PricingCard("半年付", "29.9", "每6个月", semi_annual_features)
        permanent_card = PricingCard("永久版", "99", "永久有效", permanent_features)
        
        cards_layout.addWidget(monthly_card)
        cards_layout.addWidget(semi_card)
        cards_layout.addWidget(permanent_card)
        
        main_layout.addLayout(cards_layout)
        
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
        
        # 添加激活码标题
        activation_title = QLabel("已有激活码？")
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
        
        # 添加激活码输入框
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("请输入激活码")
        self.activation_input.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 10px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                min-width: 300px;
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
        
        # 添加联系方式
        contact_label = QLabel("获取激活码请联系：example@email.com")
        contact_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #7f8c8d;
                margin-top: 10px;
            }
        """)
        contact_label.setAlignment(Qt.AlignCenter)
        activation_layout.addWidget(contact_label)
        
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