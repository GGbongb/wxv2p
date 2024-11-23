# Copyright (C) 2024 李洋 <liyo84683@gmail.com>
# All rights reserved. No modifications allowed.
#所有权利保留。禁止修改。
#本程序只能以其原始形式使用、分发和复制。
#任何试图修改、逆向工程或创建衍生作品的行为都是严格禁止的。
import sys
import os
import time
import importlib
import app
from win32com.client import Dispatch
from PyQt5.QtWidgets import QApplication, QLabel



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

if __name__ == "__main__":
    try:
        # 延迟导入模块，只在需要时导入
        print("启动主程序...")
        app_instance = app.run(show_window=True)  # 先显示主窗口
        
        # 在后台线程中检查更新
        from PyQt5.QtCore import QTimer
        def check_update():
            from components.update_manager import UpdateManager
            update_manager = UpdateManager(app_instance.main_window)
            update_info = update_manager.check_for_updates()
            
            if update_info:
                new_version, download_url, release_notes = update_info
                if update_manager.prompt_update(new_version, release_notes):
                    update_manager.download_and_install(download_url)
        
        # 延迟 2 秒检查更新
        QTimer.singleShot(2000, check_update)
        
        # 延迟创建快捷方式
        QTimer.singleShot(3000, create_desktop_shortcut)
        
        app_instance.app.exec_()  # 修改这里
            
    except Exception as e:
        print(f"启动过程出错: {e}")
    # 在开发环境中检查文件变化
    if not getattr(sys, 'frozen', False):
        while True:
            if not check_for_file_changes():
                break
