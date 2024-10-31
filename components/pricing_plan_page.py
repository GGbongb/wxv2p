from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame)
from PyQt5.QtCore import Qt

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
        
        # 添加底部空白
        main_layout.addStretch(1)