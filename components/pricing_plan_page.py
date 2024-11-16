from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QLineEdit)
from PyQt5.QtCore import Qt
from .activation_manager import ActivationManager
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap
import logging
import os
from tools.utils import resource_path
from .export_options_page import ExportOptionsPage  # 添加这行导入

logger = logging.getLogger(__name__)

class PricingPlanPage(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activation_manager = ActivationManager()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口背景色
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f6fa;
            }
        """)
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(60, 60, 60, 60)
        main_layout.setSpacing(40)
        
        # 添加顶部标题
        title = QLabel("选择您的使用方案")
        title.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #2c3e50;
                margin-bottom: 20px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 创建价格方案容器
        plans_layout = QHBoxLayout()
        plans_layout.setSpacing(30)
        
        # 试用版方案
        trial_plan = self.create_plan_card(
            "7天试用版",
            "7",
            "元",
            [
                "✓ 不限次数自由使用"
            ]
        )
        plans_layout.addWidget(trial_plan)
        
        # 永久版方案
        permanent_plan = self.create_plan_card(
            "永久版",
            "50",
            "元",
            [
                "✓ 一次付费，永久拥有"
            ]
        )
        plans_layout.addWidget(permanent_plan)
        
        # 优惠升级方案
        upgrade_plan = self.create_plan_card(
            "限时优惠",
            "40",
            "元",
            [
                "✓ 仅限试用结束7天内"
            ]
        )
        plans_layout.addWidget(upgrade_plan)
        
        main_layout.addLayout(plans_layout)
        
        # 添加二维码和说明
        payment_layout = QHBoxLayout()
        
        # 左侧支付说明
        payment_info = QLabel("扫描右侧二维码付款后，请联系客服获取激活码")
        payment_info.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #7f8c8d;
            }
        """)
        payment_layout.addWidget(payment_info)
        
        # 右侧二维码
        qr_code_label = QLabel()
        qr_code_path = resource_path(os.path.join("resources", "qrcode.png"))
        qr_code_pixmap = QPixmap(qr_code_path)
        qr_code_label.setPixmap(qr_code_pixmap.scaled(150, 150, Qt.KeepAspectRatio))
        payment_layout.addWidget(qr_code_label)
        
        main_layout.addLayout(payment_layout)
        
        # 添加激活码输入区域
        activation_container = QFrame()
        activation_container.setObjectName("activationContainer")
        activation_container.setStyleSheet("""
            QFrame#activationContainer {
                background-color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
            }
        """)
        
        activation_layout = QVBoxLayout(activation_container)
        
        # 激活码输入区域
        input_container = QHBoxLayout()
        input_container.setSpacing(15)
        
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
        main_layout.addWidget(activation_container)

    def create_plan_card(self, title, price, unit, features):
        """创建价格方案卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 40px 30px;
                min-width: 200px;
            }
            QFrame:hover {
                background-color: #ffffff;
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 价格区域
        price_container = QHBoxLayout()
        price_container.setAlignment(Qt.AlignCenter)
        
        # 价格数字
        price_label = QLabel(price)
        price_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        
        # 单位
        unit_label = QLabel(unit)
        unit_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #7f8c8d;
                margin-top: 8px;
            }
        """)
        
        price_container.addWidget(price_label)
        price_container.addWidget(unit_label)
        layout.addLayout(price_container)
        
        # 功能列表
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    color: #27ae60;
                    margin: 5px 0;
                }
            """)
            feature_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(feature_label)
        
        layout.addStretch()
        return card
    
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
            logger.debug("激活成功")
            QMessageBox.information(self, "成功", message)
            
            try:
                # 更新父窗口的激活状态
                self.parent().update_status_label()
                # 关闭对话框
                self.close()
                # 自动开始导出
                self.parent().generate_pdf()
                
                logger.debug("成功更新状态并开始生成PDF")
            except Exception as e:
                logger.error(f"更新状态时发生错误: {str(e)}", exc_info=True)
        else:
            QMessageBox.warning(self, "错误", message)
    
    def proceed_with_export(self):
        """继续导出操作"""
        from components.export_options_page import ExportOptionsPage
        export_page = ExportOptionsPage(self.parent())
        self.parent().setCentralWidget(export_page)
        # 触发PDF导出
        export_page.generate_pdf()