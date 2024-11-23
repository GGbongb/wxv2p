VERSION = "1.0.0"  # 当前版本号

class Version:
    @staticmethod
    def get_current_version():
        return VERSION
        
    @staticmethod
    def parse_version(version_str):
        """解析版本号"""
        try:
            major, minor, patch = map(int, version_str.split('.'))
            return (major, minor, patch)
        except:
            return (0, 0, 0)
            
    @staticmethod
    def compare_versions(ver1, ver2):
        """比较版本号
        返回: -1 如果 ver1 < ver2
              0 如果 ver1 = ver2
              1 如果 ver1 > ver2
        """
        v1 = Version.parse_version(ver1)
        v2 = Version.parse_version(ver2)
        return (v1 > v2) - (v1 < v2)