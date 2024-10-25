import sys
import os
import time
import importlib
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

if __name__ == "__main__":
    while True:
        app.run()
        if not check_for_file_changes():
            break