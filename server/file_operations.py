import os
import random

def create_fixed_files(data_dir, num_files):
    """创建固定的文件，包含不均匀的文件大小"""
    fixed_files = []
    for i in range(1, num_files + 1):
        filename = f'fixed_file_{i}.txt'
        if i <= 10:  # 假设前10个文件是热点文件，文件较大
            file_size = random.randint(1 * 1024 * 1024, 5 * 1024 * 1024)  # 文件大小在1MB到5MB之间
        else:
            file_size = random.randint(10 * 1024, 512 * 1024)  # 其他文件大小在10KB到512KB之间
        with open(os.path.join(data_dir, filename), 'wb') as f:
            f.write(os.urandom(file_size))
        fixed_files.append((filename, file_size))
    return fixed_files

def configure_servers_without_files(small_servers):
    """配置小服务器不包含任何文件，每次请求都向主服务器请求文件"""
    for server in small_servers:
        server.clear_files()  # 清除小服务器上的所有文件

