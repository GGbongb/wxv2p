# Copyright (C) 2024 李洋 <liyo84683@gmail.com>
# All rights reserved. No modifications allowed.
#所有权利保留。禁止修改。
#本程序只能以其原始形式使用、分发和复制。
#任何试图修改、逆向工程或创建衍生作品的行为都是严格禁止的。
import sys
import os
import time
import importlib
import requests
import subprocess
import app
from win32com.client import Dispatch

def create_desktop_shortcut():
    """创建桌面快捷方式"""
    try:
        # 获取桌面路径
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        
        # 获取程序路径
        if getattr(sys, 'frozen', False):
            # 打包后的路径
            app_path = sys.executable
        else:
            # 开发环境路径
            app_path = os.path.abspath("dist/WX聊天录屏转图片.exe")
        
        # 快捷方式路径
        shortcut_path = os.path.join(desktop_path, "WX聊天录屏转图片.lnk")
        
        # 如果快捷方式不存在，则创建
        if not os.path.exists(shortcut_path):
            try:
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = app_path
                shortcut.WorkingDirectory = os.path.dirname(app_path)
                shortcut.IconLocation = app_path
                shortcut.save()
                print("桌面快捷方式创建成功")
            except Exception as e:
                print(f"创建快捷方式失败: {e}")
    except Exception as e:
        print(f"创建快捷方式时发生错误: {e}")

def check_for_file_changes():
    """检查文件变化（仅在开发环境中使用）"""
    if getattr(sys, 'frozen', False):
        # 打包环境，直接返回 False
        return False
        
    try:
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
    except FileNotFoundError:
        # 如果找不到文件，直接返回 False
        return False

#def check_for_updates(current_version):
    """检查更新"""
    try:
        response = requests.get("https://api.github.com/repos/GGbongb/wxv2p/releases/latest")
        if response.status_code == 200:
            latest_release = response.json()
            latest_version = latest_release['tag_name']
            download_url = latest_release['assets'][0]['browser_download_url']

            if latest_version > current_version:
                return latest_version, download_url
    except Exception as e:
        print(f"检查更新时发生错误: {e}")
    return None, None

#def download_update(download_url):
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

#def install_update():
    """安装更新"""
    try:
        subprocess.call(["update.exe"])  # 运行更新程序
    except Exception as e:
        print(f"安装更新时发生错误: {e}")

if __name__ == "__main__":
    try:
        # 创建桌面快捷方式
        create_desktop_shortcut()
        
        # 检查更新
        from components.update_manager import UpdateManager
        update_manager = UpdateManager()
        latest_version, download_url = update_manager.check_for_updates()
        
        if latest_version and update_manager.prompt_update(latest_version):
            update_manager.download_and_install(download_url)
            
    except Exception as e:
        print(f"启动过程出错: {e}")
    
    # 运行主程序
    app.run()
    
    # 在开发环境中检查文件变化
    if not getattr(sys, 'frozen', False):
        while True:
            if not check_for_file_changes():
                break
