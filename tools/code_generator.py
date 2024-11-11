import random
import string
import hashlib
import datetime
import csv
import os
import json
import base64
import logging

logger = logging.getLogger(__name__)

class ActivationCodeGenerator:
    def __init__(self):
        # 修改获取根目录的方式
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 数据文件目录
        self.data_dir = os.path.join(self.root_dir, "data")
        
        # 确保数据目录存在，添加打印信息便于调试
        print(f"数据目录路径: {self.data_dir}")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 文件路径
        self.code_file = os.path.join(self.data_dir, "activation_codes.csv")
        print(f"CSV文件路径: {self.code_file}")
        self.encrypted_codes_file = os.path.join(self.data_dir, "encrypted_codes.dat")
        self.secret_key = "your_secret_key_here"
    
    def generate_code(self, plan_type):
        """生成激活码"""
        logger.debug(f"开始生成激活码，类型: {plan_type}")
        
        # 生成5位随机字符
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choice(chars) for _ in range(5))
        logger.debug(f"生成的随机部分: {random_part}")
        
        # 添加类型标识
        type_code = {
            1: "0030",  # 月付
            2: "0180",  # 半年付
            3: "9999"   # 永久版
        }.get(plan_type)
        
        # 组合激活码
        code = f"{random_part}{type_code}"
        logger.debug(f"完整的激活码: {code}")
        
        # 生成激活码的加密信息
        code_info = {
            "code": code,
            "type": plan_type,
            "generated_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 更新加密文件
        self.update_encrypted_codes(code_info)
        logger.debug("激活码信息已加密保存")

        # 保存到CSV文件新增
        self.save_code(code, plan_type)
        
        return code
    
    def update_encrypted_codes(self, new_code_info):
        """更新加密的激活码文件"""
        # 读取现有的加密数据
        existing_codes = []
        if os.path.exists(self.encrypted_codes_file):
            with open(self.encrypted_codes_file, 'rb') as f:
                try:
                    encrypted_data = f.read()
                    decrypted_data = self.decrypt_data(encrypted_data)
                    existing_codes = json.loads(decrypted_data)
                except:
                    existing_codes = []
        
        # 添加新的激活码信息
        existing_codes.append(new_code_info)
        
        # 加密并保存
        encrypted_data = self.encrypt_data(json.dumps(existing_codes))
        with open(self.encrypted_codes_file, 'wb') as f:
            f.write(encrypted_data)
    
    def encrypt_data(self, data):
        """加密数据"""
        key = hashlib.sha256(self.secret_key.encode()).digest()
        encrypted = []
        for i, c in enumerate(data):
            key_c = key[i % len(key)]
            encrypted.append(chr((ord(c) + key_c) % 256))
        return base64.b64encode(''.join(encrypted).encode())
    
    def decrypt_data(self, encrypted_data):
        """解密数据"""
        key = hashlib.sha256(self.secret_key.encode()).digest()
        encrypted = base64.b64decode(encrypted_data).decode()
        decrypted = []
        for i, c in enumerate(encrypted):
            key_c = key[i % len(key)]
            decrypted.append(chr((256 + ord(c) - key_c) % 256))
        return ''.join(decrypted)
    
    def save_code(self, code, plan_type):
        """保存生成的激活码到CSV文件"""
        print("save csv file")
        try:
            plan_names = {
                1: "月付",
                2: "半年付",
                3: "永久版"
            }
            
            file_exists = os.path.exists(self.code_file)
            print(f"CSV文件是否存在: {file_exists}")
            
            with open(self.code_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["激活码", "类型", "生成时间", "使用状态"])
                writer.writerow([
                    code,
                    plan_names[plan_type],
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "未使用"
                ])
            print(f"成功保存激活码到CSV文件: {code}")
        except Exception as e:
            print(f"保存CSV文件时出错: {str(e)}")

def main():
    generator = ActivationCodeGenerator()
    
    while True:
        print("\n激活码生成工具")
        print("1. 生成月付激活码")
        print("2. 生成半年付激活码")
        print("3. 生成永久版激活码")
        print("4. 批量生成激活码")
        print("0. 退出")
        
        choice = input("\n请选择操作: ")
        
        if choice == "0":
            break
        
        if choice in ["1", "2", "3"]:
            try:
                code = generator.generate_code(int(choice))
                print(f"\n生成的激活码: {code}")
            except Exception as e:
                print(f"生成失败: {str(e)}")
                
        elif choice == "4":
            try:
                plan_type = int(input("请选择计划类型(1=月付, 2=半年付, 3=永久版): "))
                count = int(input("请输入需要生成的数量: "))
                
                print("\n生成的激活码:")
                for i in range(count):
                    code = generator.generate_code(plan_type)
                    print(f"{i+1}. {code}")
            except Exception as e:
                print(f"生成失败: {str(e)}")
        
        else:
            print("无效的选择")

if __name__ == "__main__":
    main()
