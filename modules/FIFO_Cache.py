from collections import OrderedDict


class FIFOCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.cache = OrderedDict()
        self.server = server

        self._load_existing_files_from_db()

    def _load_existing_files_from_db(self):
        # get files from server
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT filename FROM files')
        files = cursor.fetchall()
        for file in files:
            self.cache[file[0]] = True

    def add(self, filename):
        # if exist
        if filename in self.cache:
            return

        # remove the earliest file
        if len(self.cache) >= self.max_files:
            self.evict()

        self.cache[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"fifo add {filename}. Current Cache: {list(self.cache.keys())}")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        return exists

    def evict(self):
        if self.cache:
            evicted_file, _ = self.cache.popitem(last=False)
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"fifo del {evicted_file}")
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
            return True
        return False

    def cache_content(self):
        return list(self.cache.keys())
