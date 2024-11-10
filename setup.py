from cx_Freeze import setup, Executable

# 读取 requirements.txt 文件中的依赖项
dependencies = [
    "cx_Freeze==7.2.4",
    "numpy==1.25.2",
    "opencv_python==4.10.0.84",
    "Pillow==11.0.0",
    "PyQt5==5.15.11",
    "PyQt5_sip==12.13.0",
    "reportlab==4.2.5",
    "Requests==2.32.3"
]

# 提取包名，去掉版本号
packages = [dep.split('==')[0] for dep in dependencies]

# 依赖项
build_exe_options = {
    "packages": packages,  # 添加你的依赖包
    "include_files": [
        ("resources", "resources"),  # 包含资源文件夹
    ],
}

# 设置
setup(
    name="微信录屏转图片",
    version="0.1",
    description="将微信聊天记录的录屏转为图片、PDF",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base="Win32GUI")],  # base="Win32GUI" 适用于 GUI 应用
)