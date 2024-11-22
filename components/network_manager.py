# network_manager.py
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self):
        self.api_url = "url"  # 替换为您的API地址
        self.timeout = 10  # 请求超时时间（秒）
        
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