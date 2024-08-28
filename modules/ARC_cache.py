from collections import OrderedDict


class ARCCache:
    def __init__(self, max_files, server):
        self.max_files = max_files
        self.t1 = OrderedDict()  # files that recently be requested but not a lot
        self.t2 = OrderedDict()  # files that usually & recently be requested
        self.b1 = OrderedDict()  # remove from t1
        self.b2 = OrderedDict()  # remove from t2
        self.server = server

    def add(self, filename):
        # if exist
        if filename in self.t1 or filename in self.t2:
            return

        # if full
        if len(self.t1) + len(self.t2) >= self.max_files:
            self.evict()

        if self._file_exists_in_db(filename):
            return

        # add file to the db
        self.t1[filename] = True
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        result = cursor.fetchone()
        exists = result[0] > 0 if result else False
        return exists

    def evict(self):
        if self.t1:
            evicted_file, _ = self.t1.popitem(last=False)
            self.b1[evicted_file] = True
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"arc del {evicted_file} from t1")
            return evicted_file
        elif self.t2:
            evicted_file, _ = self.t2.popitem(last=False)
            self.b2[evicted_file] = True
            cursor = self.server.conn.cursor()
            cursor.execute('DELETE FROM files WHERE filename = ?', (evicted_file,))
            self.server.conn.commit()
            # print(f"arc del {evicted_file} from t2")
            return evicted_file
        return None

    def remove(self, filename):
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
        return list(self.t1.keys()) + list(self.t2.keys())
