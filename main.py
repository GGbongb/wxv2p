import sys
import os
import time
import importlib
import requests
import subprocess
import app

def check_for_file_changes():
    last_mtime = os.path.getmtime('app.py')
    while True:
        time.sleep(1)  # 每秒检查一次
        current_mtime = os.path.getmtime('app.py')
        if current_mtime != last_mtime:
            print("检测到文件变化，正在重新加载...")
            importlib.reload(app)
            last_mtime = current_mtime
            return True
    return False

def check_for_updates(current_version):
    """检查 GitHub Releases 是否有新版本"""
    try:
        response = requests.get("https://api.github.com/repos/GGbongb/wxv2p/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release['tag_name']  # 获取最新版本号
            download_url = latest_release['assets'][0]['browser_download_url']  # 获取下载链接

            if latest_version > current_version:
                return latest_version, download_url
    except Exception as e:
        print(f"检查更新时发生错误: {e}")
    return None, None

def download_update(download_url):
    """下载更新文件"""
    try:
        response = requests.get(download_url)
        if response.status_code == 200:
            with open("update.exe", "wb") as f:  # 保存更新文件
                f.write(response.content)
            return True
    except Exception as e:
        print(f"下载更新时发生错误: {e}")
    return False

def install_update():
    """安装更新"""
    try:
        subprocess.call(["update.exe"])  # 运行更新程序
    except Exception as e:
        print(f"安装更新时发生错误: {e}")

if __name__ == "__main__":
    current_version = "0.1"  # 当前版本
    latest_version, download_url = check_for_updates(current_version)

    if latest_version:
        print(f"发现新版本: {latest_version}")
        if download_update(download_url):
            print("更新下载完成，正在安装...")
            install_update()
            sys.exit()  # 退出当前程序，等待更新程序完成
        else:
            print("更新下载失败。")
    else:
        print("当前已是最新版本。")

    while True:
        app.run()
        if not check_for_file_changes():
            break
