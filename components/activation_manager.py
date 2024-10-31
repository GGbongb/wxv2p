import hashlib
import time
import json
import os
import base64
from datetime import datetime, timedelta

class ActivationManager:
    def __init__(self):
        self.activation_file = "activation.json"
        self.encrypted_codes_file = "encrypted_codes.dat"
        self.secret_key = "your_secret_key_here"  # 与生成器使用相同的密钥
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