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
            # 添加请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 发送请求
            response = requests.get(self.url, stream=True, headers=headers, verify=True)
            response.raise_for_status()  # 检查响应状态
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            downloaded = 0
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            # 先下载到临时文件
            temp_path = self.save_path + '.tmp'
            with open(temp_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.progress_signal.emit(progress)
            
            # 下载完成后重命名
            if os.path.exists(self.save_path):
                os.remove(self.save_path)
            os.rename(temp_path, self.save_path)
            
            # 验证文件大小
            if os.path.getsize(self.save_path) != total_size:
                raise Exception("下载文件大小不正确")
                
            self.finished_signal.emit(True, "下载完成")
            
        except requests.exceptions.RequestException as e:
            print(f"下载请求错误: {e}")
            self.finished_signal.emit(False, f"下载请求错误: {str(e)}")
        except Exception as e:
            print(f"下载更新时发生错误: {e}")
            self.finished_signal.emit(False, str(e))

class UpdateManager:
    def __init__(self, parent=None):
        """初始化更新管理器
        parent: 父窗口，用于显示对话框
        """
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

    def download_and_install(self, download_url):
        """下载并安装更新"""
        try:
            # 创建进度对话框
            progress_dialog = QProgressDialog(self.parent)
            progress_dialog.setWindowTitle("更新下载")
            progress_dialog.setLabelText("正在下载更新...")
            progress_dialog.setCancelButton(None)
            progress_dialog.setRange(0, 100)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setAutoClose(False)
            
            # 确定保存路径
            if getattr(sys, 'frozen', False):
                save_dir = os.path.dirname(sys.executable)
            else:
                save_dir = os.getcwd()
            
            save_path = os.path.join(save_dir, "update.exe")
            print(f"更新文件将保存到: {save_path}")
            
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
            print(f"下载过程出错: {e}")
            QMessageBox.critical(self.parent, "错误", f"下载更新时发生错误: {e}")
            
    def handle_download_finished(self, success, message, save_path, progress_dialog):
        """处理下载完成"""
        progress_dialog.close()
        
        if success and os.path.exists(save_path):
            # 验证文件是否是有效的可执行文件
            if not os.path.getsize(save_path) > 0:
                QMessageBox.critical(
                    self.parent,
                    "更新失败",
                    "下载的更新文件无效，请稍后重试。"
                )
                return
                
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
                    subprocess.Popen([save_path], shell=True)  # 使用 shell=True
                    sys.exit(0)
                except Exception as e:
                    print(f"启动更新程序失败: {e}")
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
        
        if success and os.path.exists(save_path):
            # 验证文件是否是有效的可执行文件
            if not os.path.getsize(save_path) > 0:
                QMessageBox.critical(
                    self.parent,
                    "更新失败",
                    "下载的更新文件无效，请稍后重试。"
                )
                return
                
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
                    subprocess.Popen([save_path], shell=True)  # 使用 shell=True
                    sys.exit(0)
                except Exception as e:
                    print(f"启动更新程序失败: {e}")
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