class NearestServerScheduler:
    def __init__(self, servers):
        self.servers = servers
        # print(f"Scheduler initialized with {len(servers)} servers.")
        # for i, server in enumerate(servers):
        #     print(f"Server {i + 1} position: {server.get_position()}")

    def calculate_distance(self, position1, position2):
        """计算两个位置之间的欧几里得距离"""
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def get_next_server(self, user_position):
        """获取距离用户最近且负载最轻的服务器"""
        nearest_server = None
        shortest_distance = float('inf')
        for server in self.servers:
            server_position = server.get_position()
            distance = self.calculate_distance(server_position, user_position)
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_server = server
            elif distance == shortest_distance:
                # 如果距离相同，选择负载较轻的服务器
                if server.get_active_connections() < nearest_server.get_active_connections():
                    nearest_server = server

        # 打印调试信息以检查调度器行为
        # print(f"Selected server: {nearest_server.get_position()} with load: {nearest_server.get_active_connections()}")

        return nearest_server
