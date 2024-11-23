from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal
import requests
import logging
from .network_manager import NetworkManager
import os
import sys

logger = logging.getLogger(__name__)

class UpdateDownloader(QThread):
    """更新下载线程"""
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0
            
            with open(self.save_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.progress_signal.emit(progress)
                        
            self.finished_signal.emit(True, "下载完成")
            
        except Exception as e:
            logger.error(f"下载更新时发生错误: {str(e)}")
            self.finished_signal.emit(False, str(e))

class UpdateManager:
    def __init__(self, parent=None):
        self.parent = parent
        self.network_manager = NetworkManager()
        self.current_version = "0.1"
        
    def check_for_updates(self):
        """检查更新"""
        try:
            # 使用 COS 更新 URL
            update_url = self.network_manager.update_url
            if not update_url:
                logger.error("无法获取更新 URL")
                return None, None
                
            # 获取更新信息
            response = requests.get(
                f"{update_url}/version.json",  # 版本信息文件
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("version") > self.current_version:
                    return data.get("version"), data.get("download_url")
                    
        except Exception as e:
            logger.error(f"检查更新时发生错误: {str(e)}")
        return None, None
        
    def prompt_update(self, new_version):
        """提示用户更新"""
        reply = QMessageBox.question(
            self.parent,
            "发现新版本",
            f"发现新版本 {new_version}，是否现在更新？",
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes
        
    def download_and_install(self, download_url):
        """下载并安装更新"""
        # 创建进度对话框
        progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100, self.parent)
        progress_dialog.setWindowTitle("更新下载")
        progress_dialog.setAutoClose(True)
        
        # 创建下载线程
        save_path = os.path.join(os.path.dirname(sys.executable), "update.exe")
        downloader = UpdateDownloader(download_url, save_path)
        
        # 连接信号
        downloader.progress_signal.connect(progress_dialog.setValue)
        downloader.finished_signal.connect(
            lambda success, msg: self.handle_download_finished(success, msg, save_path)
        )
        
        # 开始下载
        downloader.start()
        progress_dialog.exec_()
        
    def handle_download_finished(self, success, message, save_path):
        """处理下载完成"""
        if success:
            reply = QMessageBox.question(
                self.parent,
                "下载完成",
                "更新已下载完成，是否立即安装？\n(安装过程中程序将关闭)",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    import subprocess
                    subprocess.Popen([save_path])
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"启动更新程序失败: {str(e)}")
                    QMessageBox.critical(self.parent, "错误", f"启动更新程序失败: {str(e)}")
        else:
            QMessageBox.critical(self.parent, "下载失败", f"更新下载失败: {message}")