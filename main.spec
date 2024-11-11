# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

added_files = [
    # 添加资源文件
    ('resources/*.png', 'resources'),  # 所有PNG图片
    ('data/encrypted_codes.dat', 'data'),  # 加密数据文件
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
        'components.video_process_thread'
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='微信录屏转图片工具',  # 您可以修改这个名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False不显示控制台
    icon='resources/logo.png'  # 可以选择一个图标
)