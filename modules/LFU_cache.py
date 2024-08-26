from collections import defaultdict, OrderedDict

class LFUCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.server = server
        self.cache = {}  # 文件到使用频率的映射
        self.freq = defaultdict(OrderedDict)  # 使用频率到文件的映射
        self.min_freq = 0  # 当前最小使用频率

    def add(self, filename):
        if filename in self.cache:
            # print(f"File {filename} is already in cache, skipping add.")
            return

        if len(self.cache) >= self.max_files:
            # print(f"Cache full. Triggering eviction before adding {filename}.")
            self.evict()

        # 检查文件是否已经存在于数据库中，避免重复插入
        if self._file_exists_in_db(filename):
            # print(f"File {filename} is already in database, skipping add.")
            return

        # 添加文件到缓存和数据库，初始频率为1
        self.cache[filename] = 1
        self.freq[1][filename] = True
        self.min_freq = 1  # 新添加的文件频率为1，更新最小频率

        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # # print(f"ADD {filename}. Current Cache: {list(self.cache.keys())}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        # # print(f"Checking if {filename} exists in database: {exists}")
        return exists

    def evict(self):
        if self.min_freq in self.freq and self.freq[self.min_freq]:
            evicted_file, _ = self.freq[self.min_freq].popitem(last=False)
            del self.cache[evicted_file]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # # print(f"DELETE {evicted_file} with frequency {self.min_freq}")
            if not self.freq[self.min_freq]:
                del self.freq[self.min_freq]
            return evicted_file
        return None

    def remove(self, filename):
        if filename in self.cache:
            freq = self.cache[filename]
            del self.cache[filename]
            del self.freq[freq][filename]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
            self.server.conn.commit()
            if not self.freq[freq] and freq == self.min_freq:
                self.min_freq += 1

    def access(self, filename):
        # print('LFU cache access:')
        # print(self.cache)
        if filename in self.cache:
            freq = self.cache[filename]
            del self.freq[freq][filename]
            self.cache[filename] = freq + 1
            self.freq[freq + 1][filename] = True
            if not self.freq[self.min_freq]:
                self.min_freq += 1
            # print(f"Cache hit for {filename}")
            return True
        # print(f"Cache miss for {filename}")
        return False

    def cache_content(self):
        return list(self.cache.keys())
