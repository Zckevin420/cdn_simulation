class NearestServerScheduler:
    def __init__(self, servers):
        self.servers = servers
        # print(f"Scheduler initialized with {len(servers)} servers.")
        # for i, server in enumerate(servers):
        #     print(f"Server {i + 1} position: {server.get_position()}")

    def calculate_distance(self, position1, position2):
        # calc dist
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def get_next_server(self, user_position):
        # get the nearest
        nearest_server = None
        shortest_distance = float('inf')
        for server in self.servers:
            server_position = server.get_position()
            distance = self.calculate_distance(server_position, user_position)
            if distance < shortest_distance:
                shortest_distance = distance
                nearest_server = server
            elif distance == shortest_distance:
                # choose the lighter load server if same distance
                if server.get_active_connections() < nearest_server.get_active_connections():
                    nearest_server = server

        # print(f"Selected server: {nearest_server.get_position()} with load: {nearest_server.get_active_connections()}")

        return nearest_server
