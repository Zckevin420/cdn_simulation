from collections import OrderedDict

class LRUCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.cache = OrderedDict()  # 使用有序字典维护LRU缓存
        self.server = server  # 服务器实例，用于操作数据库

    def add(self, filename):
        if filename in self.cache:
            # print(f"File {filename} is already in cache, skipping add.")
            # 如果文件已经在缓存中，只需将其移到末尾
            self.cache.move_to_end(filename)
            return

        # 如果缓存已满，进行淘汰
        if len(self.cache) >= self.max_files:
            # print(f"Cache full. Triggering eviction before adding {filename}.")
            self.evict()

        # 检查文件是否已经存在于数据库中，避免重复插入
        if self._file_exists_in_db(filename):
            # print(f"File {filename} is already in database, skipping add.")
            return

        # 添加新文件到缓存和数据库
        self.cache[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
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
        if self.cache:
            evicted_file, _ = self.cache.popitem(last=False)  # 移除最不常用的文件
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"DELETE {evicted_file} from cache")
            return evicted_file
        return None

    def remove(self, filename):
        """从缓存中移除文件"""
        if filename in self.cache:
            del self.cache[filename]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
            self.server.conn.commit()
            # print(f"REMOVE {filename} from cache and database")

    def access(self, filename):
        if filename in self.cache:
            # 将最近访问的文件移到末尾
            self.cache.move_to_end(filename)
            # print(f"Cache hit for {filename}")
            return True  # 缓存命中
        # print(f"Cache miss for {filename}")
        return False  # 缓存未命中

    def cache_content(self):
        """返回当前缓存内容的列表形式"""
        return list(self.cache.keys())
