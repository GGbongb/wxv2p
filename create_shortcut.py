import os
import sys
import winshell
from win32com.client import Dispatch

def create_shortcut():
    # 获取桌面路径
    desktop = winshell.desktop()
    
    # 程序路径
    path = os.path.abspath("dist/微信录屏转图片工具-律师专用.exe")
    
    # 快捷方式路径
    shortcut_path = os.path.join(desktop, "微信录屏转图片工具-律师专用.lnk")
    
    # 创建快捷方式
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = path
    shortcut.WorkingDirectory = os.path.dirname(path)
    shortcut.IconLocation = path  # 使用程序自身的图标
    shortcut.save()

if __name__ == '__main__':
    create_shortcut()