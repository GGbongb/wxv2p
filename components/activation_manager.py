import hashlib
import time
import json
import os
import base64
from datetime import datetime, timedelta
import sys

class ActivationManager:
    def __init__(self):
        # 获取程序根目录
        self.root_dir = self.get_root_dir()
        # 数据文件目录
        self.data_dir = os.path.join(self.root_dir, "data")
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 文件路径
        self.activation_file = os.path.join(self.data_dir, "activation.json")
        self.encrypted_codes_file = os.path.join(self.data_dir, "encrypted_codes.dat")
        self.secret_key = "your_secret_key_here"
        
        self.activation_info = self.load_activation_info()
    
    def get_root_dir(self):
        """获取程序根目录"""
        if getattr(sys, 'frozen', False):
            # 打包后的程序
            return os.path.dirname(sys.executable)
        else:
            # 开发环境
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def save_activation_info(self, info):
        """保存激活信息"""
        with open(self.activation_file, 'w') as f:
            json.dump(info, f)
    
    def verify_code(self, code):
        """验证激活码"""
        if not code or len(code) != 16:
            return False, "无效的激活码格式", 0
        
        try:
            # 读取加密的激活码数据
            if not os.path.exists(self.encrypted_codes_file):
                return False, "激活码验证失败", 0
            
            with open(self.encrypted_codes_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.decrypt_data(encrypted_data)
                valid_codes = json.loads(decrypted_data)
            
            # 查找匹配的激活码
            for code_info in valid_codes:
                if code_info["code"] == code:
                    # 根据类型返回不同的有效期
                    duration_days = {
                        1: 30,    # 月付
                        2: 180,   # 半年付
                        3: 36500  # 永久版
                    }.get(code_info["type"], 0)
                    
                    return True, "激活成功", duration_days
            
            return False, "无效的激活码", 0
            
        except Exception as e:
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