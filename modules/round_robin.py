# round_robin.py

class RoundRobinScheduler:
    def __init__(self, servers):
        self.servers = servers
        self.current_index = 0

    def get_next_server(self, user_position=None):
        """轮询获取下一个服务器"""
        if not self.servers:
            return None
        server = self.servers[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.servers)
        print(f"Round Robin selected server: {server.db_path}")  # 打印选中的服务器
        return server
