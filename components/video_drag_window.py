from PyQt5.QtWidgets import (QMainWindow, QLabel, QVBoxLayout, QWidget,
                             QPushButton, QMessageBox, QSizePolicy, QTextEdit, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import logging

from .fun_progress_bar import FunProgressBar
from .video_process_thread import VideoProcessThread
from .image_viewer import ImageViewer
from components.video_process_thread import VideoProcessThread
from .status_display import StatusDisplay

logger = logging.getLogger(__name__)

class VideoDragDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("微信聊天记录转图片工具")
        self.setGeometry(100, 100, 1920, 1500)

        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加状态栏（作为主窗口的一部分）
        self.status_display = StatusDisplay(self)
        self.main_layout.addWidget(self.status_display)
        
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #bdc3c7;")
        self.main_layout.addWidget(separator)
        
        # 创建内容区域的容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.main_layout.addWidget(self.content_widget)
        
        # 初始化拖放界面
        self.init_drag_drop_ui()
        
        # 初始化后立即更新激活状态
        self.update_activation_status()
        
        self.video_path = None
        self.setFocusPolicy(Qt.StrongFocus)

    def update_activation_status(self):
        """更新激活状态显示"""
        from components.activation_manager import ActivationManager
        activation_manager = ActivationManager()
        
        is_activated = activation_manager.is_activated()
        self.status_display.update_status(is_activated)
        logger.debug(f"状态已更新: 激活状态={is_activated}")

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
        
        # 创建一个水平容器用于提示信息
        hint_container = QWidget()
        hint_container.setFixedWidth(900)  # 设置一个固定宽度
        hint_container.setMinimumHeight(600)  # 添加最小高度，确保能显示所有内容    
        hint_layout = QHBoxLayout(hint_container)
        hint_layout.setContentsMargins(0, 50, 0, 50)  # 设置上边距
        
        # 添加提示信息
        self.drop_hint = QLabel("\n本软件可以从微信聊天记录录屏文件提取连续内容的截图，并可以导出为PDF或图片，无需手动截图，极大节省时间，是律师处理微信聊天证据的最佳效率工具。\n\n使用时注意：\n\n1. 对微信聊天录屏时，应匀速缓慢滑动录屏，否则导出效果不好；\n\n2. 录屏时应当从上往下翻动。", self)
        self.drop_hint.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.drop_hint.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 36px;
                line-height: 1.8;  /* 增加行高 */
                padding-left: 0px;
                margin: 30px 0;    /* 增加上下边距 */  
            }
        """)
        self.drop_hint.setWordWrap(True)  # 启用自动换行
        hint_layout.addWidget(self.drop_hint, alignment=Qt.AlignLeft)
        hint_layout.addStretch()  # 添加右侧弹性空间
        
        # 将提示信息容器添加到主布局，并居中
        text_layout.addWidget(hint_container, alignment=Qt.AlignCenter)
        
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
        self.content_layout.addWidget(self.text_container)
        
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
            
            # 更改拖放区域文字
            self.drop_area.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    font-size: 72px;
                    font-weight: bold;
                }
            """)
            self.drop_area.setText("文件已加载，点击开始截图")
            
            # 隐藏提示信息
            self.drop_hint.hide()
            
            # 显示开始按钮
            self.process_button.show()

    def process_video(self):
        if not self.video_path:
            QMessageBox.warning(self, "警告", "请先拖入视频文件！")
            return
        
        logger.debug(f"开始处理视频: {self.video_path}")
        
        # 清空内容区域而不是整个布局
        for i in reversed(range(self.content_layout.count())): 
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        # 添加进度条到内容区域
        progress_layout = QVBoxLayout()
        progress_layout.addStretch(1)
        self.progress_bar = FunProgressBar(self)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch(1)
        self.content_layout.addLayout(progress_layout)
        
        logger.debug(f"准备展示进度条")
        
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
            
            # 确保状态栏可见
            self.status_display.show()
            
            # 更新激活状态
            self.update_activation_status()
            logger.debug("更新激活状态显示")
            
            # 强制更新UI
            self.status_display.update()
            self.update()
            
            # 确保窗口保持显示
            self.show()
            logger.debug("调用 show() 方法")
            
        except Exception as e:
            logger.error(f"切换页面时发生错误: {str(e)}", exc_info=True)

    def show_image_viewer(self, frames):
        """显示图片查看器"""
        self.image_viewer = ImageViewer(frames)
        # 连接信号到槽函数
        self.image_viewer.switch_to_export_page.connect(self.show_export_page)
        self.setCentralWidget(self.image_viewer)

    def show_export_page(self):
        """显示导出选项页面"""
        from components.export_options_page import ExportOptionsPage
        export_page = ExportOptionsPage(self)
        self.setCentralWidget(export_page)

    def keyPressEvent(self, event):
        """处理键盘事件"""
        print(f"按键被按下: {event.key()}, 修饰键: {event.modifiers()}")  # 调试信息
        
        # 按下 Ctrl+Shift+D 清除激活信息
        if (event.modifiers() & Qt.ControlModifier and 
            event.modifiers() & Qt.ShiftModifier and 
            event.key() == Qt.Key_D):
            print("检测到 Ctrl+Shift+D 组合键")  # 调试信息
            try:
                from components.activation_manager import ActivationManager
                activation_manager = ActivationManager()
                if activation_manager.clear_activation():
                    self.update_activation_status()
                    QMessageBox.information(self, "提示", "激活信息已清除")
                    print("激活信息已清除")  # 调试信息
                else:
                    QMessageBox.warning(self, "警告", "清除激活信息失败")
            except Exception as e:
                print(f"发生错误: {e}")  # 调试信息
                QMessageBox.warning(self, "错误", f"清除激活信息时发生错误: {e}")