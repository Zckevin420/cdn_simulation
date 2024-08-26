from collections import OrderedDict

class ARCCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.t1 = OrderedDict()  # 最近被访问过但只访问一次的缓存
        self.t2 = OrderedDict()  # 最近被频繁访问的缓存
        self.b1 = OrderedDict()  # 从t1中移出的缓存（冷数据）
        self.b2 = OrderedDict()  # 从t2中移出的缓存（热数据）
        self.server = server  # 服务器实例，用于操作数据库

    def add(self, filename):
        if filename in self.t1 or filename in self.t2:
            # print(f"File {filename} is already in cache, skipping add.")
            return

        if len(self.t1) + len(self.t2) >= self.max_files:
            # print(f"Cache full. Triggering eviction before adding {filename}.")
            self.evict()

        # 检查文件是否已经存在于数据库中，避免重复插入
        if self._file_exists_in_db(filename):
            # print(f"File {filename} is already in database, skipping add.")
            return

        # 添加文件到缓存和数据库
        self.t1[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"ADD {filename}. Current Cache: {list(self.t1.keys()) + list(self.t2.keys())}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        # print(f"Checking if {filename} exists in database: {exists}")
        return exists

    def evict(self):
        if self.t1:
            evicted_file, _ = self.t1.popitem(last=False)
            self.b1[evicted_file] = True
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"DELETE {evicted_file} from t1")
            return evicted_file
        elif self.t2:
            evicted_file, _ = self.t2.popitem(last=False)
            self.b2[evicted_file] = True
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"DELETE {evicted_file} from t2")
            return evicted_file
        return None

    def remove(self, filename):
        """从缓存中移除文件"""
        if filename in self.t1:
            del self.t1[filename]
        elif filename in self.t2:
            del self.t2[filename]
        elif filename in self.b1:
            del self.b1[filename]
        elif filename in self.b2:
            del self.b2[filename]
        cursor = self.server.conn.cursor()
        cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
        self.server.conn.commit()

    def access(self, filename):
        # # print('ARC cache access:')
        # # print('self.t1: ', list(self.t1.keys()))
        # # print('self.t2: ', list(self.t2.keys()))
        if filename in self.t1:
            self.t2[filename] = self.t1.pop(filename)
            self.t2.move_to_end(filename)
            return True
        elif filename in self.t2:
            self.t2.move_to_end(filename)
            return True
        return False

    def cache_content(self):
        """返回当前缓存内容的列表形式"""
        return list(self.t1.keys()) + list(self.t2.keys())
