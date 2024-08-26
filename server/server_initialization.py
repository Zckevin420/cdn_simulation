import json
import math
import os
import random
import sqlite3
import numpy as np
from modules.ARC_cache import ARCCache
from modules.FIFO_Cache import FIFOCache
from modules.LFU_cache import LFUCache
from modules.LRU_cache import LRUCache
from modules.NoCache import NoCache
from modules.RR_cache import RRCache
from modules.SimpleCache import SimpleCache
from server.file_operations import create_fixed_files
from server.server import Server

def initialize_servers(data_dir, num_servers, server_positions, main_server_position, cache_size, cache_strategy_class, top_n_files):
    servers = []

    # Initialize main server with SimpleCache
    main_server = Server(f"{data_dir}/main_server.db", data_dir, main_server_position, size=1000000, max_files=cache_size, cache_strategy=None)
    main_server.cache_strategy = SimpleCache(main_server)

    # Add all initial files to the main server using SimpleCache
    fixed_files = create_fixed_files(data_dir, 100)
    for filename, file_size in fixed_files:
        main_server.cache_strategy.add(filename)

    # Ensure that the main server files are in the database before initializing caches on other servers
    main_server.list_files()

    # Initialize subsidiary servers with specified cache strategies
    for i in range(num_servers):
        server_db_path = f"{data_dir}/server_{i + 1}.db"
        small_server = Server(server_db_path, data_dir, server_positions[i], size=100000, max_files=cache_size, cache_strategy=None)

        # Apply specific cache strategy
        if cache_strategy_class == 'FIFO':
            small_server.cache_strategy = FIFOCache(cache_size, small_server)
        elif cache_strategy_class == 'RR':
            small_server.cache_strategy = RRCache(cache_size, small_server)
        elif cache_strategy_class == 'ARC':
            small_server.cache_strategy = ARCCache(cache_size, small_server)
        elif cache_strategy_class == 'LRU':
            small_server.cache_strategy = LRUCache(cache_size, small_server)
        elif cache_strategy_class == 'LFU':
            small_server.cache_strategy = LFUCache(cache_size, small_server)
        else:
            small_server.cache_strategy = NoCache()

        small_server.main_server = main_server
        servers.append(small_server)

    # Now add top_n_files to each server using the appropriate cache strategy
    for i, server in enumerate(servers, start=1):
        for filename in top_n_files:
            server.cache_strategy.add(filename)  # Use cache's add method

    return main_server, servers

def generate_positions(num_servers, grid_range):
    """Generates a list of positions for the given number of servers."""
    positions = []

    # Calculate rows and columns
    num_rows = int(np.ceil(np.sqrt(num_servers)))
    num_cols = int(np.ceil(num_servers / num_rows))

    # Calculate steps
    step_x = (2 * grid_range) / num_cols
    step_y = (2 * grid_range) / num_rows

    for i in range(num_servers):
        row = i // num_cols
        col = i % num_cols
        x = -grid_range + (col + 0.5) * step_x
        y = -grid_range + (row + 0.5) * step_y
        positions.append((x, y))

    # Ensure we have generated enough positions
    if len(positions) < num_servers:
        while len(positions) < num_servers:
            x = random.uniform(-grid_range, grid_range)
            y = random.uniform(-grid_range, grid_range)
            positions.append((x, y))

    # print(f"Generated {len(positions)} positions for {num_servers} servers.")  # 调试信息

    return positions

def generate_adaptive_hexagonal_grid(num_servers, grid_range):
    """Generate a self-adapting hexagonal grid."""
    positions = []
    num_layers = 1

    while 3 * num_layers * (num_layers + 1) < num_servers:
        num_layers += 1

    layer_spacing = grid_range / (2 * num_layers)

    for layer in range(1, num_layers + 1):
        for i in range(6):
            angle = math.pi / 3 * i
            x = layer * layer_spacing * math.cos(angle)
            y = layer * layer_spacing * math.sin(angle)
            if (x, y) == (0, 0):
                continue
            positions.append((x, y))
            for j in range(1, layer):
                x_offset = j * layer_spacing * math.cos(angle + math.pi / 3)
                y_offset = j * layer_spacing * math.sin(angle + math.pi / 3)
                new_pos = (x - x_offset, y - y_offset)
                if new_pos == (0, 0):
                    continue
                positions.append(new_pos)
                if len(positions) >= num_servers:
                    return positions[:num_servers]

    return positions[:num_servers]

def generate_positions_in_circle(num_servers, radius):
    """生成均匀分布在圆形区域内的服务器位置"""
    positions = []

    angle_increment = 2 * math.pi / num_servers  # 每个服务器的位置角度增量

    for i in range(num_servers):
        angle = i * angle_increment
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions.append((x, y))

    return positions