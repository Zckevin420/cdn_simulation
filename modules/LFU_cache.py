from collections import defaultdict, OrderedDict


class LFUCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.server = server
        self.cache = {}  # store frequency
        self.freq = defaultdict(OrderedDict)
        self.min_freq = 0

    def add(self, filename):
        # if exist
        if filename in self.cache:
            return

        # if full
        if len(self.cache) >= self.max_files:
            self.evict()

        # check db
        if self._file_exists_in_db(filename):
            return

        # initial freq == 1
        self.cache[filename] = 1
        self.freq[1][filename] = True
        # update min freq == 1
        self.min_freq = 1

        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"lfu add {filename}. Current Cache: {list(self.cache.keys())}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        return exists

    def evict(self):
        if self.min_freq in self.freq and self.freq[self.min_freq]:
            evicted_file, _ = self.freq[self.min_freq].popitem(last=False)
            del self.cache[evicted_file]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"lfu del {evicted_file}")
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
            return True
        return False

    def cache_content(self):
        return list(self.cache.keys())
