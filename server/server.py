import os
import sqlite3
from matplotlib import pyplot as plt

from modules.ARC_cache import ARCCache
from modules.FIFO_Cache import FIFOCache
from modules.NoCache import NoCache
from modules.RR_cache import RRCache

class Server:
    def __init__(self, db_path, data_dir, position, size, max_files, cache_strategy):
        self.db_path = db_path
        self.data_dir = data_dir
        self.position = position
        self.size = size
        self.max_files = max_files
        self.cache_strategy = cache_strategy if cache_strategy is not None else NoCache()
        self.main_server = None
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        self.active_connections = 0
        self.request_count = 0
        self.request_small_count = 0

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE
        )''')
        self.conn.commit()

    def _add_file_to_db(self, filename):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO files (filename) VALUES (?)', (filename,))
        self.conn.commit()

    def _remove_file_from_db(self, filename):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
        self.conn.commit()

    def _file_exists_in_db(self, filename):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        # print(f"Checking if {filename} exists in database: {exists}")
        return exists

    def add_file(self, filename):
        if not self.cache_strategy.access(filename):
            self._add_file_to_db(filename)
            self.cache_strategy.add(filename)
            # print(f"File {filename} added to cache and database.")

    def remove_file(self, filename):
        self._remove_file_from_db(filename)
        self.cache_strategy.remove(filename)

    def list_files(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT filename FROM files')
        files = cursor.fetchall()
        print(f"Files in {self.db_path}: {[file[0] for file in files]}")

    def process_request(self, filename):
        self.active_connections += 1
        try:
            # 尝试从缓存中获取文件
            cached_content = self.cache_strategy.access(filename)
            if cached_content:
                # print(flush=True)
                # print(f"Cache hit for {filename} at {self.db_path}", flush=True)
                self.request_count += 1
                self.request_small_count += 1
                return cached_content, True, True  # (内容, 找到文件, 命中缓存)

            # 如果缓存未命中，尝试从主服务器获取文件
            if self.main_server:
                # print(flush=True)
                # print(f"Cache miss for {filename}. Requesting from main server.", flush=True)
                file_content, found, _ = self.main_server.process_request(filename)
                if found:
                    # 再次检查缓存中是否已经存在文件，以避免重复添加
                    if not self.cache_strategy.access(filename):
                        self.add_file(filename)
                        self.request_count += 1
                        # print(flush=True)
                        # print(f"File {filename} added to cache and database.", flush=True)
                    return file_content, True, False  # (内容, 找到文件, 未命中缓存)

                # print(flush=True)
                # print(f"File {filename} not found on main server.", flush=True)
                return b'File not found', False, False  # (未找到内容, 未找到文件, 未命中缓存)

            # print(flush=True)
            # print(f"File {filename} not found in storage and no main server to request from.", flush=True)
            return b'File not found', False, False  # (未找到内容, 未找到文件, 未命中缓存)

        finally:
            self.active_connections -= 1

    def request_file_from_main_server(self, filename):
        if self.main_server:
            file_content, found, _ = self.main_server.process_request(filename)
            if found:
                self.add_file(filename)
                return file_content, True
            else:
                return b'File not found', False

        return b'File not found', False

    def get_position(self):
        return self.position

    def get_total_files(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files')
        result = cursor.fetchone()
        return result[0] if result else 0

    def get_active_connections(self):
        return self.active_connections


def plot_server_load_distribution(servers, filename="server_load_distribution.png"):
    server_names = [f'Server {i + 1}' for i in range(len(servers))]
    request_counts = [server.request_count for server in servers]

    plt.figure(figsize=(10, 6))
    plt.bar(server_names, request_counts, color='skyblue')
    plt.xlabel('Servers')
    plt.ylabel('Number of Requests Handled')
    plt.title('Server Load Distribution')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
