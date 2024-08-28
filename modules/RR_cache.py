import random


class RRCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.server = server
        self.cache = []
        # print("RR Cache")

    def access(self, filename):
        if filename in self.cache:
            return True
        return False

    def add(self, filename):
        if filename in self.cache:
            return
        if len(self.cache) < self.max_files:
            self.cache.append(filename)
            self.server._add_file_to_db(filename, 0)
        else:
            evicted_file = random.choice(self.cache)
            self.cache.remove(evicted_file)
            self.server._remove_file_from_db(evicted_file)
            self.cache.append(filename)
            self.server._add_file_to_db(filename, 0)
            # print(f"rr add File {filename} added to cache and database.")

    def evict(self):
        if self.cache:
            evicted_file = random.choice(self.cache)
            self.cache.remove(evicted_file)
            self.server._remove_file_from_db(evicted_file)
            return evicted_file
        return None

    def remove(self, filename):
        if filename in self.cache:
            self.cache.remove(filename)
            # print(f"rr del {filename}")

    def cache_content(self):
        return self.cache
