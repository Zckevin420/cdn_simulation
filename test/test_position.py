import math
import random

import matplotlib.pyplot as plt
import numpy as np


# Define the functions for generating positions

def generate_positions(num_servers, grid_range):
    """Generate evenly distributed server positions in a grid."""
    positions = []

    num_rows = int(np.ceil(np.sqrt(num_servers)))
    num_cols = int(np.ceil(num_servers / num_rows))

    step_x = (2 * grid_range) / num_cols
    step_y = (2 * grid_range) / num_rows

    for i in range(num_servers):
        row = i // num_cols
        col = i % num_cols
        x = -grid_range + (col + 0.5) * step_x  # Centering within the step
        y = -grid_range + (row + 0.5) * step_y  # Centering within the step
        positions.append((x, y))

    return positions


import math

def generate_adaptive_hexagonal_grid(num_servers, grid_range):
    """生成自适应的蜂窝网格，使其均匀分布在指定范围内。"""
    if num_servers < 1:
        return []

    positions = []
    num_layers = 1

    # 计算所需的层数以容纳所有服务器
    while len(positions) < num_servers:
        layer_radius = num_layers * (grid_range / num_layers)
        layer_positions = []

        for i in range(6):
            angle = math.pi / 3 * i
            for j in range(num_layers):
                x = (j + 1) * layer_radius * math.cos(angle)
                y = (j + 1) * layer_radius * math.sin(angle)
                if -grid_range <= x <= grid_range and -grid_range <= y <= grid_range:
                    layer_positions.append((x, y))
                if len(layer_positions) + len(positions) >= num_servers:
                    break
            if len(layer_positions) + len(positions) >= num_servers:
                break

        positions.extend(layer_positions)
        num_layers += 1

    # 如果数量不足，则生成随机位置补充
    while len(positions) < num_servers:
        x = random.uniform(-grid_range, grid_range)
        y = random.uniform(-grid_range, grid_range)
        if (x, y) != (0, 0):
            positions.append((x, y))

    return positions[:num_servers]

def generate_circular_positions(num_servers, radius):
    """Generate evenly distributed server positions on a circle."""
    positions = []
    angle_step = 2 * math.pi / num_servers

    for i in range(num_servers):
        angle = i * angle_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions.append((x, y))

    return positions

# Testing functions

def plot_positions(positions, title):
    """Plot the server positions."""
    x_coords = [pos[0] for pos in positions]
    y_coords = [pos[1] for pos in positions]

    plt.figure(figsize=(8, 8))
    plt.scatter(x_coords, y_coords, c='blue', marker='o')
    plt.title(title)
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.grid(True)
    plt.show()

def test_deployment_strategies():
    num_servers = 37
    grid_range = 500
    # radius = 500
    for i in range(6, num_servers):
        hex_positions = generate_adaptive_hexagonal_grid(i, grid_range)
        plot_positions(hex_positions, "Hexagonal Deployment")
    # grid_positions = generate_positions(num_servers, grid_range)
    # hex_positions = generate_adaptive_hexagonal_grid(num_servers, grid_range)
    # circular_positions = generate_circular_positions(num_servers, radius)

    # plot_positions(grid_positions, "Grid Deployment")
    # plot_positions(hex_positions, "Hexagonal Deployment")
    # plot_positions(circular_positions, "Circular Deployment")

if __name__ == '__main__':
    test_deployment_strategies()
