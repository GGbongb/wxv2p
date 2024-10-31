from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtCore import Qt

class FunProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFA500;
                border-radius: 15px;
                background-color: #FFFACD;
                text-align: center;
                padding: 1px;
                color: #FF4500;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FF6347;
                border-radius: 13px;
                margin: 2px;  /* 修复圆角问题 */
            }
        """)
        self.setFixedHeight(50)  # 增加高度以容纳文本
        self.setTextVisible(True)
        self.setFormat("%p%")
        self.setAlignment(Qt.AlignBottom | Qt.AlignCenter)  # 文本显示在底部中央
        
        # 设置文本可见并显示在进度条外部底部
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFA500;
                border-radius: 15px;
                background-color: #FFFACD;
                text-align: center;
                padding: 1px;
                color: #FF4500;
                font-weight: bold;
                margin-bottom: 20px;  /* 为底部文本留出空间 */
            }
            QProgressBar::chunk {
                background-color: #FF6347;
                border-radius: 13px;
            }
            QProgressBar {
                text-align: bottom;  /* 文本显示在底部 */
            }
        """)