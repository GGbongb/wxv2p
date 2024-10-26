from PyQt5.QtWidgets import QProgressBar

class FunProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FFA500;
                border-radius: 15px;
                background-color: #FFFACD;
                text-align: center;
                color: #FF4500;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #FF6347;
                border-radius: 13px;
            }
        """)
        self.setFixedHeight(30)
        self.setTextVisible(True)
        self.setFormat("%p%")