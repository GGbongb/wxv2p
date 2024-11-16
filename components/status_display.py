from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class StatusDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # 版本信息
        self.version_label = QLabel("v1.0.0")
        self.version_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # 促销信息
        self.promotion_label = QLabel()
        self.promotion_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                padding: 5px 10px;
            }
        """)
        
        # 激活状态
        self.activation_label = QLabel()
        self.activation_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        
        # 添加到布局
        layout.addWidget(self.version_label)
        layout.addWidget(self.promotion_label)
        layout.addStretch()  # 添加弹性空间
        layout.addWidget(self.activation_label)
        
    def update_status(self, is_activated, remaining_days=0):
        """更新状态显示"""
        if is_activated:
            if remaining_days > 3650:  # 永久版
                self.promotion_label.hide()
                status_text = "永久版"
                style = """
                    QLabel {
                        color: #27ae60;
                        font-size: 16px;
                        padding: 5px 10px;
                        background-color: #e8f5e9;
                        border-radius: 4px;
                    }
                """
            elif remaining_days == 7:  # 7天体验期
                self.promotion_label.show()
                self.promotion_label.setText("限时折扣：7天体验期内购买永久版可享受10元优惠，仅需40元")
                status_text = f"体验期剩余：{remaining_days}天"
                style = """
                    QLabel {
                        color: #e67e22;
                        font-size: 16px;
                        padding: 5px 10px;
                        background-color: #ffeaa7;
                        border-radius: 4px;
                    }
                """
            else:
                self.promotion_label.hide()
                status_text = f"剩余使用时间：{remaining_days}天"
                style = """
                    QLabel {
                        color: #27ae60;
                        font-size: 16px;
                        padding: 5px 10px;
                        background-color: #e8f5e9;
                        border-radius: 4px;
                    }
                """
        else:
            self.promotion_label.hide()
            status_text = "未激活"
            style = """
                QLabel {
                    color: #c0392b;
                    font-size: 16px;
                    padding: 5px 10px;
                    background-color: #ffebee;
                    border-radius: 4px;
                }
            """
            
        self.activation_label.setText(status_text)
        self.activation_label.setStyleSheet(style)