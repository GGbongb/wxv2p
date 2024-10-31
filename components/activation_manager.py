import hashlib
import time
import json
import os
from datetime import datetime, timedelta

class ActivationManager:
    def __init__(self):
        self.activation_file = "activation.json"
        self.activation_info = self.load_activation_info()
    
    def load_activation_info(self):
        """加载激活信息"""
        if os.path.exists(self.activation_file):
            try:
                with open(self.activation_file, 'r') as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def save_activation_info(self, info):
        """保存激活信息"""
        with open(self.activation_file, 'w') as f:
            json.dump(info, f)
    
    def verify_code(self, code):
        """验证激活码
        返回: (is_valid, message, duration_days)
        """
        if not code or len(code) != 16:  # 假设激活码长度为16位
            return False, "无效的激活码格式", 0
            
        try:
            # 解析激活码
            # 示例: XXXX-XXXX-XXXX-XXXX
            # 前12位是加密信息，后4位是类型标识
            code_type = code[-4:]  # 获取类型标识
            
            # 根据类型返回不同的有效期
            if code_type == "0030":  # 月付
                return True, "激活成功：月付版本", 30
            elif code_type == "0180":  # 半年付
                return True, "激活成功：半年版本", 180
            elif code_type == "9999":  # 永久版
                return True, "激活成功：永久版本", 36500  # 约100年
            else:
                return False, "无效的激活码", 0
                
        except Exception as e:
            return False, f"激活码验证失败: {str(e)}", 0
    
    def activate(self, code):
        """激活软件"""
        is_valid, message, duration_days = self.verify_code(code)
        
        if not is_valid:
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