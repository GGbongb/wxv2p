import os

def quick_clean(directory):
    """快速清理调试信息"""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and not file == 'quick_clean.py':
                file_path = os.path.join(root, file)
                print(f"处理文件: {file_path}")
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 替换调试代码
                replacements = {
                    'DEBUG = True': 'DEBUG = False',
                    'print(': '# print(',
                    'logger.': '# logger.',
                    'logging.': '# logging.',
                    'debug(': '# debug(',
                }
                
                modified = False
                for old, new in replacements.items():
                    if old in content:
                        content = content.replace(old, new)
                        modified = True
                
                # 如果有修改，写回文件
                if modified:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"已修改: {file_path}")

if __name__ == "__main__":
    # 指定要处理的目录
    project_dir = os.path.dirname(os.path.dirname(__file__))
    
    # 确认操作
    print(f"即将处理目录: {project_dir}")
    confirm = input("是否继续？(y/n): ")
    
    if confirm.lower() == 'y':
        quick_clean(project_dir)
        print("处理完成！")
    else:
        print("操作已取消。")
