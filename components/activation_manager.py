import hashlib
import json
import os
import base64
from datetime import datetime, timedelta
import logging
import winreg
from tools.utils import resource_path
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from .network_manager import NetworkManager
from .activation_dialog import ActivationDialog
from PyQt5.QtWidgets import QApplication
import asyncio

logger = logging.getLogger(__name__)

class ActivationManager:
    def __init__(self):
        logger.debug("初始化 ActivationManager")
        self.encrypted_codes_file = resource_path("data/encrypted_codes.dat")
        self.secret_key = "your_secret_key_here"
        self.registry_path = r"Software\WxV2P"
        self.network_manager = NetworkManager()
        self.activation_info = self.load_activation_info()
    
    def load_activation_info(self):
        """从注册表加载激活信息"""
        try:
            # 打开注册表键
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_path)
            # 读取激活信息
            value = winreg.QueryValueEx(key, "ActivationInfo")[0]
            winreg.CloseKey(key)
            return json.loads(value)
        except Exception as e:
            logger.debug(f"加载激活信息失败: {e}")
            return None
    
    def save_activation_info(self, info):
        """保存激活信息到注册表"""
        try:
            # 创建或打开注册表键
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.registry_path)
            # 保存激活信息
            winreg.SetValueEx(key, "ActivationInfo", 0, winreg.REG_SZ, json.dumps(info))
            winreg.CloseKey(key)
            logger.debug("激活信息已保存到注册表")
        except Exception as e:
            logger.error(f"保存激活信息失败: {e}")
    
    def activate(self, code):
        """激活软件"""
        logger.debug(f"开始激活，激活码: {code}")
        
        # 创建并显示进度对话框
        dialog = ActivationDialog(QApplication.activeWindow())
        dialog.show()
        QApplication.processEvents()
        
        try:
            # 验证激活码
            success, message, data = self.network_manager.activate_code(code)
            
            if not success:
                dialog.close()
                return False, message
            
            # 创建激活信息
            activation_info = {
                "code": code,
                "activation_date": data["activation_date"],
                "expiry_date": data["expiry_date"],
                "duration_days": data["duration_days"],
                "type": data["type"]
            }
            
            # 保存激活信息
            self.activation_info = activation_info
            self.save_activation_info(activation_info)
            
            dialog.close()
            return True, message
            
        except Exception as e:
            logger.error(f"激活过程中发生错误: {str(e)}", exc_info=True)
            dialog.close()
            return False, f"激活失败: {str(e)}"
    
    def is_activated(self):
        """检查是否已激活且在有效期内"""
        if not self.activation_info:
            return False
            
        try:
            expiry_date = datetime.strptime(
                self.activation_info["expiry_date"], 
                "%Y-%m-%d %H:%M:%S"
            )
            return datetime.now() < expiry_date
        except:
            return False
    
    def get_remaining_days(self):
        """获取剩余天数"""
        if not self.activation_info:
            return 0
            
        try:
            expiry_date = datetime.strptime(
                self.activation_info["expiry_date"], 
                "%Y-%m-%d %H:%M:%S"
            )
            remaining = expiry_date - datetime.now()
            return max(0, remaining.days)
        except:
            return 0
        
    def get_remaining_time(self):
        """获取剩余时间（天数和小时数）"""
        if not self.activation_info:
            return 0, 0
            
        try:
            expiry_date = datetime.strptime(
                self.activation_info["expiry_date"], 
                "%Y-%m-%d %H:%M:%S"
            )
            remaining = expiry_date - datetime.now()
            
            # 计算总小时数
            total_hours = int(remaining.total_seconds() / 3600)
            # 分离天数和小时数
            days = total_hours // 24
            hours = total_hours % 24
            
            return days, hours
        except:
            return 0, 0

    def keyPressEvent(self, event):
        # 按下 Ctrl+Shift+D 清除激活信息（仅在开发环境中）
        if event.modifiers() & Qt.ControlModifier and \
        event.modifiers() & Qt.ShiftModifier and \
        event.key() == Qt.Key_D:
            from components.activation_manager import ActivationManager
            activation_manager = ActivationManager()
            if activation_manager.clear_activation():
                self.update_activation_status()
                QMessageBox.information(self, "提示", "激活信息已清除")

    def clear_activation(self):
        """清除激活信息（仅用于开发测试）"""
        try:
            # 删除注册表项
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, self.registry_path)
            # 清空当前激活信息
            self.activation_info = None
            logger.debug("激活信息已清除")
            return True
        except WindowsError as e:
            logger.error(f"清除激活信息失败: {e}")
            return False