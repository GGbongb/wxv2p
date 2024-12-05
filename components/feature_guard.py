import logging
from datetime import datetime
from .activation_manager import ActivationManager

#logger = logging.getLogger(__name__)

class FeatureGuard:
    @staticmethod
    def can_use_premium_features():
        """检查是否可以使用高级功能（导出图片、PDF等）"""
        #logger.debug("检查高级功能使用权限")
        activation_manager = ActivationManager()
        
        if not activation_manager.is_activated():
            #logger.debug("未激活状态")
            return False
            
        # 检查是否永久版
        activation_type = activation_manager.activation_info.get('type')
        if activation_type == 3:  # 永久版
            #logger.debug("永久版用户")
            return True
            
        # 检查是否过期
        remaining_days, remaining_hours, remaining_minutes, remaining_seconds = activation_manager.get_remaining_time()
        if remaining_days <= 0 and remaining_hours <= 0 and remaining_minutes <= 0 and remaining_seconds <= 0:
           # logger.debug(f"激活已过期 (剩余: {remaining_days}天{remaining_hours}时{remaining_minutes}分{remaining_seconds}秒)")
            # 清除激活信息
            activation_manager.clear_activation()
            return False
            
        #logger.debug(f"激活状态有效，剩余: {remaining_days}天{remaining_hours}时{remaining_minutes}分{remaining_seconds}秒")
        return True