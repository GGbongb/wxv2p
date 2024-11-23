# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

author = '李洋'
email = 'liyo84683@gmail.com'
version = '1.0.0'
copyright = 'Copyright (C) 2024 李洋'


added_files = [
    # 添加资源文件
    ('resources/*.png', 'resources'),  # 所有PNG图片
    ('resources/icon.ico', 'resources'),  # 添加图标文件
    ('resources/key.bin', 'resources'),
    ('resources/api.bin', 'resources'),
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'components.activation_manager',
        'components.export_options_page',
        'components.fun_progress_bar',
        'components.image_viewer',
        'components.pdf_generator',
        'components.pricing_plan_page',
        'components.video_drag_window',
        'components.video_process_thread',
        'win32com.client',
        'win32com',
        'win32api',
        'win32con',
        'winreg',
        'pythoncom',
        'pywintypes',
		'cryptography'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加 win32com 相关文件
from PyInstaller.utils.hooks import collect_dynamic_libs
binaries = []
binaries.extend(collect_dynamic_libs('win32com'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    binaries,
    [],
    name='微信聊天录屏转图片工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='resources/icon.ico'
)