import random


class DistanceRoundRobinScheduler:
    def __init__(self, servers, initial_threshold=300, adjustment_factor=0.1):
        self.servers = servers
        self.current_index = 0
        self.threshold = initial_threshold  # 初始距离阈值
        self.adjustment_factor = adjustment_factor  # 调整因子
        self.minimum_requests_threshold = 0.2  # 最低请求阈值，百分比
        # print(f"Scheduler initialized with {len(servers)} servers.")
        # for i, server in enumerate(servers):
        #     print(f"Server {i + 1} position: {server.get_position()}")

    def calculate_distance(self, position1, position2):
        """计算两个位置之间的欧几里得距离"""
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def get_nearest_servers(self, user_position):
        """获取距离用户最近的所有服务器"""
        nearest_servers = []
        shortest_distance = float('inf')
        for server in self.servers:
            server_position = server.get_position()
            distance = self.calculate_distance(server_position, user_position)
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_servers = [server]
            elif distance <= shortest_distance + self.threshold:  # 如果在阈值范围内，加入列表
                nearest_servers.append(server)
        return nearest_servers

    def adjust_threshold(self):
        """动态调整距离阈值"""
        load_distribution = [server.get_active_connections() for server in self.servers]
        max_load = max(load_distribution)
        min_load = min(load_distribution)

        # 根据负载差异调整阈值
        if max_load > 1.5 * min_load:
            self.threshold *= (1 + self.adjustment_factor)  # 增大阈值
        else:
            self.threshold *= (1 - self.adjustment_factor)  # 减小阈值

        self.threshold = max(50, min(self.threshold, 1000))

    def get_next_server(self, user_position):
        """选择下一个合适的服务器"""
        nearest_servers = self.get_nearest_servers(user_position)

        if not nearest_servers:  # 如果没有服务器在阈值内，直接选择最近的服务器
            nearest_servers = self.servers
            nearest_servers.sort(key=lambda server: self.calculate_distance(user_position, server.get_position()))
            selected_server = nearest_servers[0]
        else:
            # 根据负载选择合适的服务器
            nearest_servers.sort(key=lambda server: server.get_active_connections())
            lightest_servers = [server for server in nearest_servers if
                                server.get_active_connections() == nearest_servers[0].get_active_connections()]
            selected_server = random.choice(lightest_servers)

        # 计算总请求数
        total_requests = sum(server.request_count for server in self.servers)

        # 确保 Server 1 不会长期处于低负载
        if total_requests > 0:  # 添加检查，确保 total_requests 不为零
            if selected_server == self.servers[0] and (
                    self.servers[0].request_count / total_requests) < self.minimum_requests_threshold:
                # 如果 Server 1 负载低于某个阈值，强制分配给它一定的请求
                selected_server = self.servers[0]

        # 动态调整阈值
        self.adjust_threshold()

        return selected_server

