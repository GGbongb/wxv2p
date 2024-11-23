from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal, Qt
import requests
import logging
from .network_manager import NetworkManager
import os
import sys
from .version import Version, VERSION
from urllib.parse import quote


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
        self.current_version = VERSION
        
    def check_for_updates(self):
        """检查更新"""
        print("开始检查更新...")
        try:
            base_url = self.network_manager.update_url
            if not base_url:
                print("无法获取更新 URL")
                return None
                
            print(f"正在获取版本信息...")
            response = requests.get(
                f"{base_url}/version.json",
                timeout=10
            )
            print(f"服务器响应: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"版本信息: {data}")
                    new_version = data.get("version")
                    
                    if not new_version:
                        print("未找到版本信息")
                        return None
                        
                    print(f"当前版本: {self.current_version}, 最新版本: {new_version}")
                    
                    if Version.compare_versions(new_version, self.current_version) > 0:
                        file_path = quote(data.get("file_path", ""))
                        download_url = f"{base_url}/{file_path}"
                        notes = "\n".join(data.get("release_notes", []))
                        print(f"发现新版本，下载地址: {download_url}")
                        return (new_version, download_url, notes)
                    else:
                        print("当前已是最新版本")
                        
                except ValueError as e:
                    print(f"解析版本信息失败: {e}")
                    print(f"响应内容: {response.text}")
                    
        except Exception as e:
            print(f"检查更新时发生错误: {str(e)}")
            
        return None
        
    def prompt_update(self, new_version, release_notes):
        """提示用户更新"""
        message = f"发现新版本 {new_version}\n\n更新内容：\n{release_notes}\n\n是否现在更新？"
        reply = QMessageBox.question(
            self.parent,
            "发现新版本",
            message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes
        
def download_and_install(self, download_url):
    """下载并安装更新"""
    try:
        # 创建进度对话框
        progress_dialog = QProgressDialog(self.parent)
        progress_dialog.setWindowTitle("更新下载")
        progress_dialog.setLabelText("正在下载更新...")
        progress_dialog.setCancelButton(None)  # 禁用取消按钮
        progress_dialog.setRange(0, 100)
        progress_dialog.setWindowModality(Qt.WindowModal)  # 模态对话框
        progress_dialog.setMinimumDuration(0)  # 立即显示
        progress_dialog.setAutoClose(False)  # 不自动关闭
        
        # 根据运行环境确定保存路径
        if getattr(sys, 'frozen', False):
            save_path = os.path.join(os.path.dirname(sys.executable), "update.exe")
        else:
            save_path = os.path.join(os.getcwd(), "update.exe")
            
        # 创建下载线程
        downloader = UpdateDownloader(download_url, save_path)
        
        # 连接信号
        downloader.progress_signal.connect(progress_dialog.setValue)
        downloader.finished_signal.connect(
            lambda success, msg: self.handle_download_finished(success, msg, save_path, progress_dialog)
        )
        
        # 开始下载
        downloader.start()
        progress_dialog.exec_()
        
    except Exception as e:
        QMessageBox.critical(self.parent, "错误", f"下载更新时发生错误: {e}")
        
def handle_download_finished(self, success, message, save_path, progress_dialog):
    """处理下载完成"""
    progress_dialog.close()
    
    if success:
        reply = QMessageBox.question(
            self.parent,
            '更新准备就绪',
            '更新已下载完成，点击"确定"开始安装。\n安装过程中程序将自动关闭，安装完成后请重新启动程序。',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 显示最后的提示
                QMessageBox.information(
                    self.parent,
                    "开始更新",
                    "程序即将关闭并开始安装更新，请稍候...",
                    QMessageBox.Ok
                )
                
                # 启动更新程序
                import subprocess
                subprocess.Popen([save_path])
                sys.exit(0)
            except Exception as e:
                QMessageBox.critical(
                    self.parent,
                    "错误",
                    f"启动更新程序失败: {e}\n请手动运行更新程序: {save_path}"
                )
    else:
        QMessageBox.critical(
            self.parent,
            "更新失败",
            f"下载更新失败: {message}\n请稍后重试或联系开发者获取帮助。"
        )