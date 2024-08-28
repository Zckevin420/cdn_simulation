from collections import OrderedDict


class LRUCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.cache = OrderedDict()
        self.server = server

    def add(self, filename):
        if filename in self.cache:
            # move to the end if exist
            self.cache.move_to_end(filename)
            return

        # evict if full
        if len(self.cache) >= self.max_files:
            self.evict()

        # check db
        if self._file_exists_in_db(filename):
            return

        self.cache[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"lru add {filename}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        return exists

    def evict(self):
        if self.cache:
            evicted_file, _ = self.cache.popitem(last=False)  # remove the top file
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"lru del {evicted_file}")
            return evicted_file
        return None

    def remove(self, filename):
        if filename in self.cache:
            del self.cache[filename]
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (filename,))
            self.server.conn.commit()

    def access(self, filename):
        if filename in self.cache:
            # move to the end
            self.cache.move_to_end(filename)
            return True
        return False

    def cache_content(self):
        return list(self.cache.keys())
