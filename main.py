import os
import shutil
import time
from collections import Counter
import gc
import numpy as np
import random

import pandas as pd
from matplotlib import pyplot as plt
from server.user_db import get_user_position
from server.user_simulation import UserSimulation, calculate_response_time_std
from server.server_initialization import initialize_servers, generate_positions, generate_adaptive_hexagonal_grid
from server.user_initialization import initialize_users, generate_user_requests_zipf, generate_zipf_distribution, \
    generate_user_requests
from server.file_operations import create_fixed_files, configure_servers_without_files
from server.plotting import plot_positions
from modules.distance_round_robin import DistanceRoundRobinScheduler
from modules.nearest_server import NearestServerScheduler


def get_top_n_files(user_requests, n):
    file_counter = Counter()

    for requests in user_requests.values():
        file_counter.update(requests)

    top_n_files = [file for file, count in file_counter.most_common(n)]

    return top_n_files


def plot_server_request_distribution(servers, output_dir, filename="server_request_distribution.png"):
    server_distribution_dir = os.path.join(output_dir, "server_load_distribution")
    os.makedirs(server_distribution_dir, exist_ok=True)

    server_ids = [f"Server {i + 1}" for i in range(len(servers))]
    request_counts = [server.request_count for server in servers]

    plt.figure(figsize=(12, 6))
    plt.bar(server_ids, request_counts, color='skyblue')
    plt.xlabel('Servers')
    plt.ylabel('Number of Requests')
    plt.title('Server Request Distribution')
    plt.xticks(rotation=45)
    plt.tight_layout()

    save_path = os.path.join(server_distribution_dir, filename)
    plt.savefig(save_path)
    plt.close()


def plot_scalability_analysis(results, filename="scalability_analysis.png"):
    num_servers_list = [r[0] for r in results]
    average_response_times = [r[1] * 1000 / (r[3]) for r in results]  # r[3] 是总请求数
    response_time_stds = [r[2] for r in results]

    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Number of Servers')
    ax1.set_ylabel('Average Response Time (ms)', color=color)
    ax1.plot(num_servers_list, average_response_times, 'o-', color=color, label='Avg Response Time')
    ax1.tick_params(axis='y', labelcolor=color)

    ax1.set_ylim([min(average_response_times) - 10, max(average_response_times) + 10])

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Standard Deviation (s)', color=color)
    ax2.plot(num_servers_list, response_time_stds, 'o--', color=color, label='Std Dev')
    ax2.tick_params(axis='y', labelcolor=color)

    ax2.set_ylim([min(response_time_stds) - 0.01, max(response_time_stds) + 0.01])

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    plt.title('Scalability Analysis: Servers vs Response Time')
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.subplots_adjust(top=0.9)
    plt.savefig(filename)
    plt.close()


def plot_rectangular_response_time(num_servers_list, average_response_time_list, std_dev_list, filename):
    fig, ax1 = plt.subplots()

    color = 'tab:blue'
    ax1.set_xlabel('Number of Servers')
    ax1.set_ylabel('Average Response Time (ms)', color=color)
    ax1.plot(num_servers_list, average_response_time_list, color=color, label='Avg Response Time', marker='o')
    ax1.tick_params(axis='y', labelcolor=color)

    ax1.set_ylim([min(average_response_time_list) - 10, max(average_response_time_list) + 10])

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Standard Deviation (s)', color=color)
    ax2.plot(num_servers_list, std_dev_list, color=color, linestyle='--', label='Std Dev', marker='o')
    ax2.tick_params(axis='y', labelcolor=color)

    ax2.set_ylim([min(std_dev_list) - 0.01, max(std_dev_list) + 0.01])

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    plt.title('Rectangular Grid - Average Response Time & Std Dev')
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.savefig(filename)
    plt.close()


#
# def plot_hexagonal_response_time(num_servers_list, average_response_time_list, std_dev_list, filename):
#     """绘制完整六边形网格布局的平均响应时间和标准差"""
#     # 完整六边形的服务器数量
#     valid_num_servers = {6, 18, 36, 60}
#
#     # 筛选出有效的服务器数量对应的数据
#     filtered_servers = [num for num in num_servers_list if num in valid_num_servers]
#     filtered_avg_time = [average_response_time_list[i] for i, num in enumerate(num_servers_list) if num in valid_num_servers]
#     filtered_std_dev = [std_dev_list[i] for i, num in enumerate(num_servers_list) if num in valid_num_servers]
#
#     fig, ax1 = plt.subplots()
#
#     color = 'tab:blue'
#     ax1.set_xlabel('Number of Servers')
#     ax1.set_ylabel('Average Response Time (ms)', color=color)
#     ax1.plot(filtered_servers, filtered_avg_time, 'o-', color=color, label='Avg Response Time')
#     ax1.tick_params(axis='y', labelcolor=color)
#
#     ax2 = ax1.twinx()
#     color = 'tab:orange'
#     ax2.set_ylabel('Standard Deviation (s)', color=color)
#     ax2.plot(filtered_servers, filtered_std_dev, 'o--', color=color, label='Std Dev')
#     ax2.tick_params(axis='y', labelcolor=color)
#
#     fig.tight_layout()
#     fig.legend(loc='upper right', bbox_to_anchor=(1, 1), bbox_transform=ax1.transAxes)
#     plt.title('Hexagonal Grid - Average Response Time & Std Dev')
#     plt.savefig(filename)
#     plt.close()


def plot_ribbon_graph(num_servers_list, strategies_data, scheduler_type):
    plt.figure(figsize=(12, 8))
    for strategy_name, (avg_times, _) in strategies_data.items():
        plt.plot(num_servers_list, avg_times, label=strategy_name)
    plt.xlabel('Number of Servers')
    plt.ylabel('Average Response Time (ms)')
    plt.title(f'Average Response Time Comparison under {scheduler_type} Scheduler')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'{scheduler_type}_avg_response_time_comparison.png')
    plt.close()

    plt.figure(figsize=(12, 8))
    for strategy_name, (_, std_devs) in strategies_data.items():
        plt.plot(num_servers_list, std_devs, label=strategy_name)
    plt.xlabel('Number of Servers')
    plt.ylabel('Standard Deviation (s)')
    plt.title(f'Standard Deviation Comparison under {scheduler_type} Scheduler')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'{scheduler_type}_std_dev_comparison.png')
    plt.close()


def verify_zipf_distribution(user_requests, fixed_request_list, zipf_s, filename="files_distribution.png"):
    actual_file_counts = Counter()

    for key, value in user_requests.items():
        if isinstance(value, list):
            actual_file_counts[key] = len(value)
        elif isinstance(value, int):
            actual_file_counts[key] = value

    # ideal graph
    num_files = len(fixed_request_list)
    ideal_weights = generate_zipf_distribution(num_files, s=zipf_s)
    total_requests = sum(actual_file_counts.values())
    ideal_file_counts = ideal_weights * total_requests

    files = range(1, num_files + 1)

    plt.figure(figsize=(12, 6))
    plt.plot(files, [actual_file_counts.get(file, 0) for file in fixed_request_list], 'o-', label='Actual Distribution')
    plt.plot(files, ideal_file_counts, 'x--', label='Ideal Zipf Distribution')
    plt.xlabel('File Rank')
    plt.ylabel('Number of Requests')
    plt.title('Comparison of Actual and Ideal Zipf Distribution')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_hit_rate(servers, num_servers, output_dir):
    hit_rate_dir = os.path.join(output_dir, 'hit_rate')
    os.makedirs(hit_rate_dir, exist_ok=True)
    small_server_hit_rates = []

    for server in servers:
        if server.request_count > 0:  # avoid divide 0
            small_server_hit_rate = (server.request_small_count / server.request_count) * 100
        else:
            small_server_hit_rate = 0.0
        small_server_hit_rates.append(small_server_hit_rate)

    plt.figure(figsize=(12, 6))
    plt.bar([f"Server {i + 1}" for i in range(len(servers))], small_server_hit_rates, color='green')
    plt.xlabel('Servers')
    plt.ylabel('Hit Rate (%)')
    plt.title(f'Small Server Hit Rate Distribution for {num_servers} Servers')
    plt.xticks(rotation=45)
    plt.tight_layout()

    hit_rate_filename = os.path.join(hit_rate_dir, f"small_server_hit_rate_{num_servers}_servers.png")
    plt.savefig(hit_rate_filename)  # 保存图表
    plt.close()


# def plot_rectangular_ribbon_graph(num_servers_list, strategies_data, filename):
#     plt.figure(figsize=(12, 8))
#
#     for strategy_name, (avg_times, _) in strategies_data.items():
#         # 使用 num_servers_list 过滤 avg_times 以匹配长度
#         filtered_avg_times = [avg_times[num_servers_list.index(ns)] for ns in num_servers_list if ns in num_servers_list]
#
#         if len(num_servers_list) != len(filtered_avg_times):
#             print(f"Warning: Length mismatch in strategy {strategy_name}. Expected {len(num_servers_list)}, got {len(filtered_avg_times)}. Skipping plot.")
#             continue
#
#         plt.plot(num_servers_list, filtered_avg_times, label=strategy_name)
#         plt.fill_between(num_servers_list, filtered_avg_times, alpha=0.2)
#
#     plt.xlabel('Number of Servers')
#     plt.ylabel('Average Response Time (ms)')
#     plt.title('Rectangular Grid - Average Response Time Comparison')
#     plt.legend(loc='upper left')
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig(filename)
#     plt.close()
#
# def plot_rectangular_std_ribbon_graph(num_servers_list, strategies_data, filename):
#     plt.figure(figsize=(12, 8))
#
#     for strategy_name, (_, std_devs) in strategies_data.items():
#         # 使用 num_servers_list 过滤 std_devs 以匹配长度
#         filtered_std_devs = [std_devs[num_servers_list.index(ns)] for ns in num_servers_list if ns in num_servers_list]
#
#         if len(num_servers_list) != len(filtered_std_devs):
#             print(f"Warning: Length mismatch in strategy {strategy_name}. Expected {len(num_servers_list)}, got {len(filtered_std_devs)}. Skipping plot.")
#             continue
#
#         plt.plot(num_servers_list, filtered_std_devs, label=strategy_name)
#         plt.fill_between(num_servers_list, filtered_std_devs, alpha=0.2)
#
#     plt.xlabel('Number of Servers')
#     plt.ylabel('Standard Deviation (s)')
#     plt.title('Rectangular Grid - Standard Deviation Comparison')
#     plt.legend(loc='upper left')
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig(filename)
#     plt.close()

def filter_valid_data(num_servers_list, data):
    return [data[i] for i in range(len(data)) if i < len(num_servers_list)]


def plot_rectangular_ribbon_graph(num_servers_list, strategies_data, filename):
    plt.figure(figsize=(12, 8))
    for strategy_name, (avg_times, _) in strategies_data.items():
        filtered_avg_times = filter_valid_data(num_servers_list, avg_times)
        if len(num_servers_list) != len(filtered_avg_times):
            continue
        plt.plot(num_servers_list, filtered_avg_times, label=strategy_name)
    plt.xlabel('Number of Servers')
    plt.ylabel('Average Response Time (ms)')
    plt.title('Rectangular Grid - Average Response Time Comparison')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def plot_rectangular_std_ribbon_graph(num_servers_list, strategies_data, filename):
    plt.figure(figsize=(12, 8))
    for strategy_name, (_, std_devs) in strategies_data.items():
        filtered_std_devs = filter_valid_data(num_servers_list, std_devs)
        if len(num_servers_list) != len(filtered_std_devs):
            continue
        plt.plot(num_servers_list, filtered_std_devs, label=strategy_name)
    plt.xlabel('Number of Servers')
    plt.ylabel('Standard Deviation (s)')
    plt.title('Rectangular Grid - Standard Deviation Comparison')
    plt.legend(loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()


def reset_server_state(servers):
    for server in servers:
        server.request_count = 0
        server.active_connections = 0


def main_multi_file_request(num_requests_per_user, num_users, max_files_per_server, cache_strategies, scheduler_types):
    start_time = time.time()

    data_dir = 'data'
    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)
    os.makedirs(data_dir, exist_ok=True)

    user_db_path = 'user_data.db'
    fixed_users, user_positions = initialize_users(user_db_path, num_users, grid_size=1000)

    fixed_request_list = [f'fixed_file_{i}.txt' for i in range(1, 101)]

    user_requests = generate_user_requests_zipf(fixed_request_list, num_users, num_requests_per_user, zipf_s=1.0)
    # user_requests = generate_user_requests(fixed_request_list, num_users, num_requests_per_user)

    avg_response_times = {}
    std_devs = {}

    ribbon_graph_dir = os.path.join('results')
    os.makedirs(ribbon_graph_dir, exist_ok=True)

    output_dir = f'results'
    output_dir1 = f'results'

    for layout_type in ['grid']:
        avg_response_times[layout_type] = {}
        std_devs[layout_type] = {}

        for cache_strategy in cache_strategies:
            avg_response_times[layout_type][cache_strategy] = {}
            std_devs[layout_type][cache_strategy] = {}

            rectangular_num_servers_list = []
            rectangular_average_response_time_list = []
            rectangular_std_dev_list = []

            for scheduler_type in scheduler_types:

                # initialize
                avg_response_times[layout_type][cache_strategy][scheduler_type] = []
                std_devs[layout_type][cache_strategy][scheduler_type] = []

                output_dir = f'results/{layout_type}/{cache_strategy}_{scheduler_type}'
                os.makedirs(output_dir, exist_ok=True)
                position_dir = os.path.join(output_dir, 'position')
                server_load_dir = os.path.join(output_dir, 'server_load')
                os.makedirs(position_dir, exist_ok=True)
                os.makedirs(server_load_dir, exist_ok=True)

                all_num_servers_list = []
                all_average_response_time_list = []
                all_std_dev_list = []
                results = []
                hit_rates_data = []

                for num_servers in range(6, 65):  # set num of servers

                    if os.path.exists(data_dir):
                        shutil.rmtree(data_dir)
                    os.makedirs(data_dir, exist_ok=True)

                    server_positions = generate_positions(num_servers, grid_range=500)

                    top_n_files = get_top_n_files(user_requests, n=20)

                    main_server, servers = initialize_servers(data_dir, num_servers, server_positions,
                                                              main_server_position=(0, 0),
                                                              cache_size=max_files_per_server,
                                                              cache_strategy_class=cache_strategy,
                                                              top_n_files=top_n_files)

                    reset_server_state(servers)

                    # print(f"Main Server: ({main_server.db_path}):")
                    # main_server.list_files()
                    # for idx, server in enumerate(servers):
                    #     print(f"Server {idx + 1} ({server.db_path}):")
                    #     server.list_files()

                    # set scheduler to simulation
                    user_simulation = UserSimulation(servers, fixed_request_list, user_db_path, request_interval=0.5,
                                                     scheduler=scheduler_type, user_requests=user_requests)

                    total_response_time, std_dev_response_time = user_simulation.simulate_requests(
                        num_requests_per_user)
                    average_response_time = total_response_time * 1000 / (num_requests_per_user * num_users)

                    user_server_connections = []
                    for username, requests in user_requests.items():
                        user_pos = get_user_position(user_db_path, username)
                        server = user_simulation.scheduler.get_next_server(user_pos)
                        server_index = servers.index(server)
                        user_server_connections.append((user_pos, server_index))

                    plot_positions(user_positions, server_positions[:num_servers], user_server_connections,
                                   filename=os.path.join(position_dir, f"positions_{num_servers}.png"))

                    # get the rate of finding files after simulation
                    hit_rate = (user_simulation.total_hits / user_simulation.total_requests) * 100
                    hit_rates_data.append((num_servers, hit_rate))

                    all_num_servers_list.append(num_servers)
                    all_average_response_time_list.append(average_response_time)
                    all_std_dev_list.append(std_dev_response_time)

                    avg_response_times[layout_type][cache_strategy][scheduler_type].append(average_response_time)
                    std_devs[layout_type][cache_strategy][scheduler_type].append(std_dev_response_time)

                    results.append(
                        (num_servers, total_response_time, std_dev_response_time, num_requests_per_user * num_users))

                    print(
                        f"Layout: {layout_type}, Cache: {cache_strategy}, Scheduler: {scheduler_type}, Servers: {num_servers}, "
                        f"Avg response time: {average_response_time:.4f}ms, Std Dev: {std_dev_response_time:.4f}s.")

                    # for i, server in enumerate(servers):
                    # print(
                    #     f"Server {i + 1}: request_count = {server.request_count}, request_small_count = {server.request_small_count}")

                    plot_hit_rate(servers, num_servers, output_dir)

                    num_rows = int(np.sqrt(num_servers))
                    num_cols = int(np.ceil(num_servers / num_rows))
                    if num_rows * num_cols == num_servers:
                        rectangular_num_servers_list.append(num_servers)
                        rectangular_average_response_time_list.append(average_response_time)
                        rectangular_std_dev_list.append(std_dev_response_time)

                    # user_simulation.print_server_hit_rates()

                    plot_server_request_distribution(servers, output_dir=output_dir,
                                                     filename=f"server_request_distribution_{num_servers}.png")
                    distribution_filename = os.path.join(output_dir,
                                                         f"file_request_distribution_{num_servers}_servers.png")

                    verify_zipf_distribution(user_simulation.request_counts, fixed_request_list, zipf_s=1.0,
                                             filename=distribution_filename)

                    # shut all and delete data folder
                    for server in servers:
                        server.conn.close()
                    main_server.conn.close()

                    time.sleep(0.2)

                    if os.path.exists(data_dir):
                        shutil.rmtree(data_dir)

                plot_scalability_analysis(results, filename=os.path.join(output_dir, "scalability_analysis.png"))

                # if using grid
                if layout_type == 'grid':
                    plot_rectangular_response_time(rectangular_num_servers_list, rectangular_average_response_time_list,
                                                   rectangular_std_dev_list,
                                                   filename=os.path.join(output_dir1, "rectangular_response_time.png"))

        for scheduler_type in scheduler_types:
            strategies_data = {
                cache_strategy: (
                    avg_response_times['grid'][cache_strategy][scheduler_type],
                    std_devs['grid'][cache_strategy][scheduler_type]
                )
                for cache_strategy in cache_strategies
            }

            plot_ribbon_graph(list(range(6, 65)), strategies_data, scheduler_type)

            plot_rectangular_ribbon_graph(
                rectangular_num_servers_list,
                strategies_data,
                filename=os.path.join(output_dir, "rectangular_ribbon_graph.png")
            )

            plot_rectangular_std_ribbon_graph(
                rectangular_num_servers_list,
                strategies_data,
                filename=os.path.join(output_dir, "rectangular_std_ribbon_graph.png")
            )

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total runtime: {total_time:.2f} seconds.")


if __name__ == '__main__':
    num_requests_per_user = 5
    num_users = 35000
    max_files_per_server = 20

    cache_strategies = ['ARC', 'LFU', 'FIFO']
    scheduler_types = ['distance_round_robin']

    main_multi_file_request(num_requests_per_user=num_requests_per_user, num_users=num_users,
                            max_files_per_server=max_files_per_server,
                            cache_strategies=cache_strategies, scheduler_types=scheduler_types)
