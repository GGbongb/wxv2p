# activation_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer

class ActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("正在激活")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("正在验证激活码...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # 显示忙碌状态
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def set_status(self, text: str):
        self.status_label.setText(text)