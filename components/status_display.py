from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup
from PyQt5.QtGui import QColor
import logging

logger = logging.getLogger(__name__)

class AnimatedPromotionLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 16px;
                padding: 5px 10px;
                border-radius: 4px;
                background-color: #fff3e0;
            }
        """)
        
        # 创建动画组
        self.animation_group = QParallelAnimationGroup(self)
        
        # 颜色渐变动画
        self.color_animation = QPropertyAnimation(self, b"styleSheet")
        self.color_animation.setDuration(1500)  # 1.5秒一个周期
        self.color_animation.setLoopCount(-1)   # 永久循环
        
        # 设置颜色渐变关键帧
        style_template = """
            QLabel {
                color: %s;
                font-size: 16px;
                padding: 5px 10px;
                border-radius: 4px;
                background-color: %s;
            }
        """
        
        # 正确设置关键帧
        self.color_animation.setStartValue(style_template % ('#e74c3c', '#fff3e0'))
        self.color_animation.setKeyValueAt(0.5, style_template % ('#d35400', '#ffe0b2'))
        self.color_animation.setEndValue(style_template % ('#e74c3c', '#fff3e0'))
        
        # 缩放动画
        self.scale_animation = QPropertyAnimation(self, b"minimumWidth")
        self.scale_animation.setDuration(1500)
        self.scale_animation.setLoopCount(-1)
        self.scale_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 将两个动画添加到动画组
        self.animation_group.addAnimation(self.color_animation)
        self.animation_group.addAnimation(self.scale_animation)
        
    def start_animation(self):
        """开始动画"""
        # 设置缩放动画的范围（基于文字宽度）
        base_width = self.fontMetrics().width(self.text()) + 40
        self.scale_animation.setStartValue(base_width)
        self.scale_animation.setEndValue(base_width + 20)
        
        self.animation_group.start()
        
    def stop_animation(self):
        """停止动画"""
        self.animation_group.stop()

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
        
        # 促销信息（使用新的动画标签）
        self.promotion_label = AnimatedPromotionLabel()
        
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
        layout.addStretch()
        layout.addWidget(self.activation_label)
        
    def update_status(self, is_activated):
        """更新状态显示"""
        from components.activation_manager import ActivationManager
        activation_manager = ActivationManager()
        remaining_days, remaining_hours = activation_manager.get_remaining_time()
        
        if is_activated:
            if remaining_days > 3650:  # 永久版
                self.promotion_label.hide()
                self.promotion_label.stop_animation()
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
            elif remaining_days == 7 or (remaining_days == 6 and remaining_hours > 0):  # 7天体验期
                self.promotion_label.show()
                self.promotion_label.setText("限时折扣：7天体验期内购买永久版可享受10元优惠，仅需40元")
                self.promotion_label.start_animation()
                status_text = f"体验期剩余：{remaining_days}天{remaining_hours}小时"
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
                self.promotion_label.stop_animation()
                status_text = f"剩余使用时间：{remaining_days}天{remaining_hours}小时"
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
            self.promotion_label.stop_animation()
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