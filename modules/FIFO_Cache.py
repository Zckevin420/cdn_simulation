from collections import OrderedDict

class FIFOCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.cache = OrderedDict()  # 使用 OrderedDict 来维护 FIFO 顺序
        self.server = server  # 直接传入 Server 实例

        self._load_existing_files_from_db()

    def _load_existing_files_from_db(self):
        """从数据库加载现有文件到缓存"""
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT filename FROM files')
        files = cursor.fetchall()
        for file in files:
            self.cache[file[0]] = True
        # print(f"Initial cache loaded from database: {list(self.cache.keys())}")

    def add(self, filename):
        # 如果文件已经在缓存中，直接返回，不重复添加
        if filename in self.cache:
            # print(f"File {filename} is already in cache, skipping add.")
            return

        # 如果缓存已满，移除最早的文件
        if len(self.cache) >= self.max_files:
            # print(f"Cache full. Triggering eviction before adding {filename}.")
            self.evict()

        # 添加文件到缓存和数据库
        self.cache[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"ADD {filename}. Current Cache: {list(self.cache.keys())}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        # print(f"Checking if {filename} exists in database: {exists}")
        return exists

    def evict(self):
        # 从缓存中移除最早的文件并删除数据库中的记录
        if self.cache:
            evicted_file, _ = self.cache.popitem(last=False)
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"DELETE {evicted_file}")
            return evicted_file
        return None

    def remove(self, filename):
        """从缓存中移除文件"""
        if filename in self.cache:
            del self.cache[filename]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
            self.server.conn.commit()

    def access(self, filename):
        if filename in self.cache:
            return True
        return False

    def cache_content(self):
        """返回当前缓存内容的列表形式"""
        return list(self.cache.keys())
