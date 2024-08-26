class SimpleCache:
    def __init__(self, server):
        self.server = server
        self.files = set()

    def add(self, filename):
        if filename not in self.files:
            # 首先检查数据库中是否已经存在该文件
            if not self._file_exists_in_db(filename):
                self._add_file_to_db(filename)  # 添加文件到主服务器的数据库中
                self.files.add(filename)
                # print(f"[SimpleCache] File {filename} added to the main server and cache.")
            # else:
                # print(f"[SimpleCache] File {filename} already exists in the database.")
        # else:
            # print(f"[SimpleCache] File {filename} already in the cache.")

    def _file_exists_in_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM files WHERE filename = ?', (filename,))
        return cursor.fetchone()[0] > 0

    def _add_file_to_db(self, filename):
        cursor = self.server.conn.cursor()
        cursor.execute('INSERT INTO files (filename) VALUES (?)', (filename,))
        self.server.conn.commit()
        # print(f"[SimpleCache] File {filename} added to database.")

    def access(self, filename):
        # print('self.files', self.files)
        if filename in self.files:
            # print(f"[SimpleCache] Cache hit for {filename}.")
            return True
        # print(f"[SimpleCache] Cache miss for {filename}.")
        return False

    def evict(self):
        # SimpleCache does not handle eviction logic since it is not required for the main server
        pass
