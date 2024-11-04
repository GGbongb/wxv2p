from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget,
                             QPushButton, QMessageBox, QSizePolicy, QTextEdit, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import logging

from .fun_progress_bar import FunProgressBar
from .video_process_thread import VideoProcessThread
from .image_viewer import ImageViewer
from components.video_process_thread import VideoProcessThread

logger = logging.getLogger(__name__)

class VideoDragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信聊天记录转图片工具")
        self.setGeometry(100, 100, 1920,1500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 添加顶部状态栏
        self.init_status_bar()
        
        self.init_drag_drop_ui()

        self.video_path = None

    def init_status_bar(self):
        """初始化顶部状态栏"""
        status_layout = QHBoxLayout()
        
        # 版本信息
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 5px;
            }
        """)
        
        # 添加弹性空间
        status_layout.addWidget(version_label)
        status_layout.addStretch()
        
        # 激活状态
        self.activation_status = QLabel()
        self.activation_status.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 5px 10px;
                border-radius: 4px;
            }
        """)
        self.update_activation_status()
        
        status_layout.addWidget(self.activation_status)
        
        # 将状态栏添加到主布局
        self.layout.addLayout(status_layout)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #bdc3c7;")
        self.layout.addWidget(separator)

    def update_activation_status(self):
        """更新激活状态显示"""
        from components.activation_manager import ActivationManager
        activation_manager = ActivationManager()
        
        if activation_manager.is_activated():
            remaining_days = activation_manager.get_remaining_days()
            if remaining_days > 3650:  # 超过10年视为永久版
                status_text = "永久版"
            else:
                status_text = f"剩余使用时间：{remaining_days}天"
            
            self.activation_status.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    font-size: 22px;
                    padding: 5px 10px;
                    background-color: #e8f5e9;
                    border-radius: 4px;
                }
            """)
        else:
            status_text = "未激活"
            self.activation_status.setStyleSheet("""
                QLabel {
                    color: #c0392b;
                    font-size: 22px;
                    padding: 5px 10px;
                    background-color: #ffebee;
                    border-radius: 4px;
                }
            """)
        
        self.activation_status.setText(status_text)

    def init_drag_drop_ui(self):
        # 创建一个容器用于文字显示
        self.text_container = QWidget()
        text_layout = QVBoxLayout(self.text_container)
        
        # 添加上方空白
        text_layout.addStretch(4)
        
        # 拖放文字标签
        self.drop_area = QLabel("拖曳微信录屏文件到此", self)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-size: 72px;
                font-weight: bold;
            }
        """)
        text_layout.addWidget(self.drop_area)
        
        # 添加文字和按钮之间的空白
        text_layout.addStretch(3)
        
        # 开始按钮
        self.process_button = QPushButton("开始截图", self)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f;
                color: white;
                border: none;
                padding: 30px 60px;
                border-radius: 8px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f39c12;
            }
        """)
        self.process_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.process_button.clicked.connect(self.process_video)
        self.process_button.hide()  # 初始时隐藏按钮
        text_layout.addWidget(self.process_button, alignment=Qt.AlignCenter)
        
        # 添加底部空白
        text_layout.addStretch(4)
        
        # 将容器添加到主布局
        self.layout.addWidget(self.text_container)
        
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            self.video_path = urls[0].toLocalFile()
            # 保持文字样式和位置不变，只更改内容
            self.drop_area.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-size: 72px;
                    font-weight: bold;
                }
            """)
            self.drop_area.setText("文件已加载，点击开始截图")
            self.process_button.show()  # 显示开始按钮

    def process_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先拖入视频文件！")
            return
        
        logger.debug(f"开始处理视频: {self.video_path}")

        # 隐藏激活状态标签
        self.activation_status.hide()  # 添加这一行
        # Clear the layout
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget:
                logger.debug(f"移除控件: {widget}")
                widget.setParent(None)
            else:
                logger.debug("没有找到控件")   
        self.layout.update()
                  
        logger.debug(f"准备展示进度条")
        
    # 创建一个新的布局来居中进度条
        progress_layout = QVBoxLayout()
        progress_layout.addStretch(1)  # 添加弹性空间以居中
        self.progress_bar = FunProgressBar(self)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch(1)  # 添加弹性空间以居中

        # 将进度条布局添加到主布局
        self.layout.addLayout(progress_layout)

        self.animation = QPropertyAnimation(self.progress_bar, b"value")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(100)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)

        self.thread = VideoProcessThread(self.video_path)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.show_images)
        
        #添加日志显示功能
        #self.log_display = QTextEdit(self)
        #self.log_display.setReadOnly(True)
        #self.layout.addWidget(self.log_display)

        #def display_log(message):
        #     self.log_display.append(message)

        #self.thread.log_message.connect(display_log)
        logger.debug("启动视频处理线程")    
        self.thread.start()
        logger.debug("视频处理线程已启动")

    def update_progress(self, value):
        self.animation.setStartValue(self.progress_bar.value())
        self.animation.setEndValue(value)
        self.animation.start()

    def show_images(self, frames):
        self.image_viewer = ImageViewer(frames)
        # 连接信号到处理函数
        self.image_viewer.switch_to_export_page.connect(self.switch_to_export_page)
        self.setCentralWidget(self.image_viewer)

    def switch_to_export_page(self):
        """处理切换到导出页面的信号"""
        logger.debug("开始切换到导出页面")
        try:
            from components.export_options_page import ExportOptionsPage
            export_page = ExportOptionsPage(self)
            logger.debug("创建 ExportOptionsPage 成功")
            
            self.setCentralWidget(export_page)
            logger.debug("设置 centralWidget 成功")
            
            # 更新激活状态
            self.update_activation_status()
            logger.debug("更新激活状态显示")
            
            # 确保窗口保持显示
            self.show()
            logger.debug("调用 show() 方法")
            
        except Exception as e:
            logger.error(f"切换页面时发生错误: {str(e)}", exc_info=True)
