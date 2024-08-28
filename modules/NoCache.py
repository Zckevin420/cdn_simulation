class NoCache:
    def access(self, filename):
        # print('No cache access:')
        # print('NoCache')
        return False

    def add(self, filename):
        # print(f"[no] add {filename}")
        return None

    def evict(self):
        # print("[no] No evict")
        return None

    def remove(self, filename):
        # print(f"[no] remove {filename}")
        return None

    def cache_content(self):
        return []
