class SimpleCache:
    def __init__(self, server):
        self.server = server
        self.files = set()

    def add(self, filename):
        if filename not in self.files:
            # check if exist
            if not self._file_exists_in_db(filename):
                self._add_file_to_db(filename)
                self.files.add(filename)

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        return cursor.fetchone()[0] > 0

    def _add_file_to_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"simple add {filename}")

    def access(self, filename):
        # print('self.files', self.files)
        if filename in self.files:
            return True
        return False

    def evict(self):
        pass
