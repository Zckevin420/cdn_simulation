import random


class DistanceRoundRobinScheduler:
    def __init__(self, servers, initial_threshold=300, adjustment_factor=0.1):
        self.servers = servers
        self.current_index = 0
        self.threshold = initial_threshold
        self.adjustment_factor = adjustment_factor
        self.minimum_requests_threshold = 0.2
        # print(f"Scheduler initialized with {len(servers)} servers.")
        # for i, server in enumerate(servers):
        #     print(f"Server {i + 1} position: {server.get_position()}")

    def calculate_distance(self, position1, position2):
        # calc distance
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def get_nearest_servers(self, user_position):
        nearest_servers = []
        shortest_distance = float('inf')
        for server in self.servers:
            server_position = server.get_position()
            distance = self.calculate_distance(server_position, user_position)
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_servers = [server]
            elif distance <= shortest_distance + self.threshold:
                nearest_servers.append(server)
        return nearest_servers

    def adjust_threshold(self):
        load_distribution = [server.get_active_connections() for server in self.servers]
        max_load = max(load_distribution)
        min_load = min(load_distribution)

        # change threshold by load
        if max_load > 1.5 * min_load:
            self.threshold *= (1 + self.adjustment_factor)
        else:
            self.threshold *= (1 - self.adjustment_factor)

        self.threshold = max(50, min(self.threshold, 1000))

    def get_next_server(self, user_position):
        nearest_servers = self.get_nearest_servers(user_position)

        if not nearest_servers:
            # choose the nearest when no server in threshold
            nearest_servers = self.servers
            nearest_servers.sort(key=lambda server: self.calculate_distance(user_position, server.get_position()))
            selected_server = nearest_servers[0]
        else:
            # base load choose next server
            nearest_servers.sort(key=lambda server: server.get_active_connections())
            lightest_servers = [server for server in nearest_servers if
                                server.get_active_connections() == nearest_servers[0].get_active_connections()]
            selected_server = random.choice(lightest_servers)

        # total_requests = sum(server.request_count for server in self.servers)

        self.adjust_threshold()

        return selected_server
