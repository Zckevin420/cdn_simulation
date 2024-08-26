import random

class RRCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.server = server
        self.cache = []
        # print("RR Cache")

    def access(self, filename):
        if filename in self.cache:
            return True  # 缓存命中
        return False  # 缓存未命中

    def add(self, filename):
        if filename in self.cache:
            # print('Already cached')
            return  # 如果文件已经在缓存中，忽略
        if len(self.cache) < self.max_files:
            self.cache.append(filename)
            self.server._add_file_to_db(filename, 0)  # 添加到数据库
            # print(f"[RR ADD] File {filename} added to cache and database.")
        else:
            evicted_file = random.choice(self.cache)  # 随机选择一个文件进行替换
            self.cache.remove(evicted_file)
            self.server._remove_file_from_db(evicted_file)  # 从数据库中删除
            self.cache.append(filename)
            self.server._add_file_to_db(filename, 0)  # 添加到数据库
            # print(f"[RR ADD] File {filename} added to cache and database.")

    def evict(self):
        if self.cache:
            evicted_file = random.choice(self.cache)  # 随机选择一个文件进行移除
            self.cache.remove(evicted_file)
            self.server._remove_file_from_db(evicted_file)  # 从数据库中删除
            return evicted_file
        return None

    def remove(self, filename):
        """从缓存中移除文件"""
        if filename in self.cache:
            self.cache.remove(filename)
            print(f"[RR REMOVE] File {filename} removed from cache.")

    def cache_content(self):
        """返回当前缓存内容的列表形式"""
        return self.cache
