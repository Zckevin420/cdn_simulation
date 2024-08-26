class NoCache:
    def access(self, filename):
        # print('No cache access:')
        # print('NoCache')
        # print(f"[NoCache] Attempting to access {filename}, but caching is disabled.")
        return False  # Always miss

    def add(self, filename):
        # print(f"[No]Adding {filename} to cache using strategy {type(self).__name__}")
        return None

    def evict(self):
        # print("[NoCache] No eviction necessary, caching is disabled.")
        return None

    def remove(self, filename):
        # print(f"[No]Remove {filename} to cache using strategy {type(self).__name__}")
        return None

    def cache_content(self):
        return []
