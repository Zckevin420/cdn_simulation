import os
import random


def create_fixed_files(data_dir, num_files):
    # create files, but different size
    fixed_files = []
    for i in range(1, num_files + 1):
        filename = f'fixed_file_{i}.txt'
        if i <= 10:  # the top 10 file will be larger size
            file_size = random.randint(1 * 1024 * 1024, 5 * 1024 * 1024)  # pick random size
        else:
            file_size = random.randint(10 * 1024, 512 * 1024)  # random size
        with open(os.path.join(data_dir, filename), 'wb') as f:
            f.write(os.urandom(file_size))
        fixed_files.append((filename, file_size))
    return fixed_files


def configure_servers_without_files(small_servers):
    # set servers without any file
    for server in small_servers:
        server.clear_files()
