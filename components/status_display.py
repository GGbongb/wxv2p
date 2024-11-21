from PyQt5.QtWidgets import (QLabel, QWidget, QHBoxLayout, QVBoxLayout, 
                           QFrame, QLineEdit, QPushButton, QMessageBox, QMainWindow)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint, QRect, QTimer
from PyQt5.QtGui import QColor, QPixmap, QCursor
import os
from tools.utils import resource_path
import logging

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class HoverInfoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.setVisible(False)
        
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 添加鼠标事件追踪
        self.setMouseTracking(True)
        
    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建内容容器
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = QLabel("永久版特惠")
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 28px;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(title)
        
        # 价格信息
        price_info = QLabel("限时优惠价：40元（原价50元）")
        price_info.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        content_layout.addWidget(price_info)
        
        # 功能描述
        features = QLabel("✓ 一次付费，永久使用\n✓ 无限次数导出PDF和图片\n✓ 免费获取后续更新")
        features.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 20px;
                line-height: 1.8;
            }
        """)
        content_layout.addWidget(features)
        
        # 二维码
        qr_label = QLabel()
        qr_code_path = resource_path(os.path.join("resources", "qrcode.png"))
        qr_pixmap = QPixmap(qr_code_path)
        qr_pixmap = qr_pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        qr_label.setPixmap(qr_pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(qr_label)
        
        # 扫码说明
        scan_hint = QLabel("扫描二维码添加客服购买")
        scan_hint.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
            }
        """)
        scan_hint.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(scan_hint)
        
        # 添加分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ecf0f1;")
        content_layout.addWidget(separator)
        
        # 添加激活区域
        activation_widget = QWidget()
        activation_layout = QVBoxLayout(activation_widget)
        activation_layout.setSpacing(10)
        
        # 激活标题
        activation_title = QLabel("已购买？立即激活")
        activation_title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        activation_layout.addWidget(activation_title)
        
        # 激活码输入框和按钮的水平布局
        input_layout = QHBoxLayout()
        
        # 激活码输入框
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("请输入激活码")
        self.activation_input.setMinimumHeight(40)
        self.activation_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 16px;
            }
        """)
        input_layout.addWidget(self.activation_input)
        
        # 激活按钮
        activate_button = QPushButton("激活")
        activate_button.setCursor(Qt.PointingHandCursor)
        activate_button.clicked.connect(self.activate_code)
        activate_button.setMinimumHeight(40)
        activate_button.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        input_layout.addWidget(activate_button)
        
        activation_layout.addLayout(input_layout)
        content_layout.addWidget(activation_widget)
        
        # 添加内容容器到主布局
        main_layout.addWidget(content_widget)
        
        # 添加阴影效果
        self.setGraphicsEffect(self.create_shadow())
        
    def create_shadow(self):
        """创建阴影效果"""
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        return shadow

    def activate_code(self):
        """激活码验证处理"""
        logger.debug("开始激活码验证流程")
        from components.activation_manager import ActivationManager
        activation_manager = ActivationManager()
        
        code = self.activation_input.text().strip()
        if not code:
            QMessageBox.warning(self, "提示", "请输入激活码")
            return
            
        success, message = activation_manager.activate(code)
        logger.debug(f"激活结果: success={success}, message={message}")
        
        if success:
            # 先更新状态
            if hasattr(self, 'main_window'):
                logger.debug("找到主窗口引用，开始更新状态")
                self.main_window.update_activation_status()
                
            # 然后显示成功消息
            QMessageBox.information(self, "成功", message)
            
            # 最后安全地隐藏悬浮框
            self.setVisible(False)
            logger.debug("悬浮框已隐藏")
            
        else:
            QMessageBox.warning(self, "错误", message)

    def leaveEvent(self, event):
        """鼠标离开悬浮框"""
        # 获取鼠标当前位置
        mouse_pos = QCursor.pos()
        
        # 检查鼠标是否在悬浮框内
        widget_rect = self.geometry()
        global_rect = QRect(self.mapToGlobal(widget_rect.topLeft()),
                            self.mapToGlobal(widget_rect.bottomRight()))
        
        if not global_rect.contains(mouse_pos):
            self.hide()
            logger.debug("鼠标离开悬浮框区域，隐藏悬浮框")

class AnimatedPromotionLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug(f"AnimatedPromotionLabel 初始化, parent={parent}")
        
        # 初始化动画
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(1000)  # 1秒
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 延迟创建悬浮框
        self.hover_widget = None
        
        # 设置初始样式
        self.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                font-size: 24px;
                padding: 5px 10px;
                background-color: #ffeaa7;
                border-radius: 4px;
            }
        """)
        
    def enterEvent(self, event):
        """鼠标进入标签时创建并显示悬浮框"""
        # 如果悬浮框还没创建，就创建它
        if self.hover_widget is None:
            # 查找主窗口
            from components.video_drag_window import VideoDragDropWindow
            main_window = None
            parent_widget = self
            
            while parent_widget:
                logger.debug(f"查找主窗口，当前组件: {type(parent_widget)}")
                if isinstance(parent_widget, VideoDragDropWindow):
                    main_window = parent_widget
                    break
                parent_widget = parent_widget.parent()
                
            if main_window:
                logger.debug("成功找到主窗口，创建悬浮框")
                self.hover_widget = HoverInfoWidget()
                self.hover_widget.setParent(main_window)
                self.hover_widget.main_window = main_window
                # 设置窗口标志
                self.hover_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip | Qt.WindowStaysOnTopHint)
                self.hover_widget.setAttribute(Qt.WA_TranslucentBackground)
            else:
                logger.error("未找到主窗口，无法创建悬浮框")
                return
                
        # 计算悬浮框位置
        pos = self.mapToGlobal(QPoint(0, self.height() + 5))
        pos.setX(pos.x() + (self.width() - self.hover_widget.width()) // 2)
        
        self.hover_widget.move(pos)
        self.hover_widget.show()
        logger.debug("显示悬浮框")
        
    def leaveEvent(self, event):
        """鼠标离开标签"""
        if self.hover_widget:
            # 获取鼠标当前位置
            mouse_pos = QCursor.pos()
            
            # 检查鼠标是否在悬浮框内
            hover_widget_rect = QRect(self.hover_widget.pos(), self.hover_widget.size())
            
            if not hover_widget_rect.contains(mouse_pos):
                self.hover_widget.hide()
                logger.debug("隐藏悬浮框")

    def start_animation(self):
        """开始动画效果"""
        logger.debug("开始促销标签动画")
        current_pos = self.pos()
        
        # 设置动画起始和结束位置
        self.animation.setStartValue(current_pos)
        end_pos = current_pos + QPoint(10, 0)  # 向右移动10像素
        self.animation.setEndValue(end_pos)
        
        # 设置动画完成后的回调
        #self.animation.finished.connect(self._reverse_animation)
        
        # 开始动画
        self.animation.start()
        
    def stop_animation(self):
        """停止动画"""
        logger.debug("停止促销标签动画")
        if self.animation.state() == QPropertyAnimation.Running:
                self.animation.stop()

class StatusDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

        # 添加定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_countdown)
        self.timer.start(1000)  # 每秒更新一次
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # 版本信息
        self.version_label = QLabel("v1.0.0")
        self.version_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 24px;
                padding: 5px;
            }
        """)
        
        # 促销信息（使用新的动画标签）
        self.promotion_label = AnimatedPromotionLabel()
        
        # 激活状态
        self.activation_label = QLabel()
        self.activation_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
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
        logger.debug(f"StatusDisplay.update_status 被调用: is_activated={is_activated}")

        from components.activation_manager import ActivationManager
        activation_manager = ActivationManager()
        remaining_days, remaining_hours, remaining_minutes, remaining_seconds = activation_manager.get_remaining_time()
        activation_type = activation_manager.activation_info.get('type') if activation_manager.activation_info else None
        
        logger.debug(f"更新状态显示: 已激活={is_activated}, 类型={activation_type}")
        
        # 更新状态显示
        if is_activated:
            if activation_type == 3:  # 永久版
                # 确保促销标签被隐藏和停止动画
                if hasattr(self, 'promotion_label'):
                    self.promotion_label.hide()
                    self.promotion_label.stop_animation()
                status_text = "永久版"
                style = """
                    QLabel {
                        color: #27ae60;
                        font-size: 24px;
                        padding: 5px 10px;
                        background-color: #e8f5e9;
                        border-radius: 4px;
                    }
                """
                logger.debug("已设置为永久版状态")
            elif activation_type == 0:  # 7天体验期
                self.promotion_label.show()
                self.promotion_label.setText("限时折扣：7天体验期内购买永久版可享受10元优惠，仅需40元")
                self.promotion_label.start_animation()
                status_text = f"体验期剩余：{remaining_days}天{remaining_hours}小时{remaining_minutes}分钟{remaining_seconds}秒"
                style = """
                    QLabel {
                        color: #e67e22;
                        font-size: 24px;
                        padding: 5px 10px;
                        background-color: #ffeaa7;
                        border-radius: 4px;
                    }
                """
            else:
                self.promotion_label.hide()
                self.promotion_label.stop_animation()
                status_text = f"剩余使用时间：{remaining_days}天{remaining_hours}小时{remaining_minutes}分钟{remaining_seconds}秒"
                style = """
                    QLabel {
                        color: #27ae60;
                        font-size: 24px;
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
                    font-size: 24px;
                    padding: 5px 10px;
                    background-color: #ffebee;
                    border-radius: 4px;
                }
            """
            
        self.activation_label.setText(status_text)
        self.activation_label.setStyleSheet(style)
        
        # 强制更新UI
        self.activation_label.update()
        self.update()
        logger.debug(f"状态显示已更新: {status_text}")

    def update_countdown(self):
        """更新倒计时显示"""
        if not hasattr(self, 'activation_label'):
            return
            
        from components.activation_manager import ActivationManager
        from components.feature_guard import FeatureGuard
        
        activation_manager = ActivationManager()
        
        # 使用 FeatureGuard 检查是否可用（包含过期检查）
        if not FeatureGuard.can_use_premium_features():
            # 如果功能不可用（过期或未激活），显示未激活状态
            self.promotion_label.hide()
            self.promotion_label.stop_animation()
            
            status_text = "未激活"
            style = """
                QLabel {
                    color: #c0392b;
                    font-size: 24px;
                    padding: 5px 10px;
                    background-color: #ffebee;
                    border-radius: 4px;
                }
            """
            self.activation_label.setText(status_text)
            self.activation_label.setStyleSheet(style)
            logger.debug("激活已过期，更新为未激活状态")
            return
            
        # 以下是未过期的情况
        activation_type = activation_manager.activation_info.get('type')
        if activation_type == 3:  # 永久版不需要倒计时
            return
            
        remaining_days, remaining_hours, remaining_minutes, remaining_seconds = activation_manager.get_remaining_time()
        
        if activation_type == 0:  # 7天体验期
            # 显示促销标签
            self.promotion_label.show()
            self.promotion_label.setText("限时折扣：7天体验期内购买永久版可享受10元优惠，仅需40元")
            self.promotion_label.start_animation()
            
            status_text = f"体验期剩余：{remaining_days}天{remaining_hours}小时{remaining_minutes}分钟{remaining_seconds}秒"
            style = """
                QLabel {
                    color: #e67e22;
                    font-size: 24px;
                    padding: 5px 10px;
                    background-color: #ffeaa7;
                    border-radius: 4px;
                }
            """
        else:  # 其他类型的激活
            self.promotion_label.hide()
            self.promotion_label.stop_animation()
            
            status_text = f"剩余使用时间：{remaining_days}天{remaining_hours}小时{remaining_minutes}分钟{remaining_seconds}秒"
            style = """
                QLabel {
                    color: #27ae60;
                    font-size: 24px;
                    padding: 5px 10px;
                    background-color: #e8f5e9;
                    border-radius: 4px;
                }
            """
            
        self.activation_label.setText(status_text)
        self.activation_label.setStyleSheet(style)
        logger.debug(f"更新倒计时显示: {status_text}")