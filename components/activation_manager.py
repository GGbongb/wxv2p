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

logger = logging.getLogger(__name__)

class ActivationManager:
    def __init__(self):
        logger.debug("初始化 ActivationManager")
        self.encrypted_codes_file = resource_path("data/encrypted_codes.dat")
        self.secret_key = "your_secret_key_here"
        self.registry_path = r"Software\WxV2P"
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
    
    def verify_code(self, code):
        """验证激活码"""
        logger.debug(f"开始验证激活码: {code}")
        
        if not code or len(code) != 9:
            logger.warning(f"无效的激活码格式，长度为: {len(code) if code else 0}")
            return False, "无效的激活码格式", 0
            
        try:
            # 读取加密的激活码数据
            if not os.path.exists(self.encrypted_codes_file):
                logger.error(f"找不到加密文件: {self.encrypted_codes_file}")
                return False, "激活码验证失败", 0
            
            logger.debug("开始读取加密文件")
            with open(self.encrypted_codes_file, 'rb') as f:
                encrypted_data = f.read()
                logger.debug("成功读取加密数据")
                
                decrypted_data = self.decrypt_data(encrypted_data)
                logger.debug("成功解密数据")
                
                valid_codes = json.loads(decrypted_data)
                logger.debug(f"解析到的有效激活码数量: {len(valid_codes)}")
            
            # 查找匹配的激活码
            for code_info in valid_codes:
                logger.debug(f"检查激活码: {code_info['code']}")
                if code_info["code"] == code:
                    logger.debug("找到匹配的激活码")
                    duration_days = {
                        1: 30,    # 月付
                        2: 180,   # 半年付
                        3: 36500  # 永久版
                    }.get(code_info["type"], 0)
                    
                    return True, "激活成功", duration_days
            
            logger.warning("未找到匹配的激活码")
            return False, "无效的激活码", 0
            
        except Exception as e:
            logger.error(f"验证过程中发生错误: {str(e)}", exc_info=True)
            return False, f"激活码验证失败: {str(e)}", 0
    
    def decrypt_data(self, encrypted_data):
        """解密数据"""
        key = hashlib.sha256(self.secret_key.encode()).digest()
        encrypted = base64.b64decode(encrypted_data).decode()
        decrypted = []
        for i, c in enumerate(encrypted):
            key_c = key[i % len(key)]
            decrypted.append(chr((256 + ord(c) - key_c) % 256))
        return ''.join(decrypted)
    
    def activate(self, code):
        """激活软件"""
        logger.debug(f"尝试激活软件激活码: {code}")
        is_valid, message, duration_days = self.verify_code(code)
        
        if not is_valid:
            logger.warning(f"激活失败: {message}")
            return False, message
            
        # 创建激活信息
        activation_info = {
            "code": code,
            "activation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_date": (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S"),
            "duration_days": duration_days
        }
        
        # 保存激活信息
        self.activation_info = activation_info
        self.save_activation_info(activation_info)
        logger.debug("激活信息已保存到注册表")
        
        return True, message
    
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