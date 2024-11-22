# network_manager.py
from cryptography.fernet import Fernet
import requests
import logging
from typing import Optional, Dict, Any
from tools.utils import resource_path

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self):
        self.api_url = "url"  # 替换为您的API地址
        self.timeout = 10  # 请求超时时间（秒）

    def _get_api_url(self) -> str:
        """获取解密后的 API URL"""
        try:
            # 从资源文件读取加密的 URL
            key_path = resource_path("resources/key.bin")
            url_path = resource_path("resources/api.bin")
            
            # 读取密钥和加密的 URL
            with open(key_path, 'rb') as f:
                key = f.read()
            with open(url_path, 'rb') as f:
                encrypted_url = f.read()
                
            # 解密
            fernet = Fernet(key)
            decrypted_url = fernet.decrypt(encrypted_url)
            
            return decrypted_url.decode()
            
        except Exception as e:
            logger.error(f"获取 API URL 失败: {str(e)}")
            return "https://fallback-url.com"  # 备用 URL
        
    def check_network(self) -> bool:
        """检查网络连接"""
        try:
            requests.get("https://www.baidu.com", timeout=5)
            return True
        except:
            return False
            
    def activate_code(self, code: str) -> tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        在线激活码验证
        返回: (是否成功, 消息, 激活数据)
        """
        try:
            if not self.check_network():
                return False, "无法连接到网络，请检查网络连接后重试", None
                
            response = requests.get(
                f"{self.api_url}/activate",
                params={"code": code},
                timeout=self.timeout
            )
            
            data = response.json()
            
            if data.get("success"):
                return True, data.get("message", "激活成功"), data.get("data")
            else:
                return False, data.get("message", "激活失败"), None
                
        except requests.RequestException as e:
            logger.error(f"网络请求错误: {str(e)}")
            return False, "网络请求失败，请稍后重试", None
        except Exception as e:
            logger.error(f"激活过程出错: {str(e)}")
            return False, "激活过程出现错误", None