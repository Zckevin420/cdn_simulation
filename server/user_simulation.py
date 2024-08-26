import os
import random
import time
import math
import sqlite3

import numpy as np
import pandas as pd

from server.user_db import get_user_position
from modules.nearest_server import NearestServerScheduler
from modules.round_robin import RoundRobinScheduler
from modules.distance_round_robin import DistanceRoundRobinScheduler
from collections import Counter


import matplotlib.pyplot as plt

class UserSimulation:
    def __init__(self, servers, request_list, user_db_path, request_interval, scheduler, user_requests=None):
        self.servers = servers
        self.request_list = request_list
        self.user_db_path = user_db_path
        self.request_interval = request_interval
        self.scheduler = scheduler  # 保存调度器实例
        self.user_requests = user_requests or {}
        self.request_counts = {str(filename): 0 for filename in request_list}
        self.user_response_times = []  # 每次请求的响应时间
        self.total_hits = 0
        self.total_requests = 0
        self.total_misses = 0
        self.request_counts_by_server = {i: 0 for i in range(len(servers))}  # 初始化请求计数字典
        self.hit_counts_by_server = [0] * len(servers)
        self.request_log = []  # 用于存储每次请求的日志信息
        self.file_request_counts = Counter()

        if scheduler == 'nearest':
            self.scheduler = NearestServerScheduler(servers)
        elif scheduler == 'round_robin':
            self.scheduler = RoundRobinScheduler(servers)
        elif scheduler == 'distance_round_robin':
            self.scheduler = DistanceRoundRobinScheduler(servers)
        else:
            raise ValueError("Unsupported scheduler type")

    def calculate_response_time(self, distance):
        """根据距离计算响应时间"""
        return 2 * ((distance // 1000) + (distance % 1000) / 1000.0)

    def send_request(self, request, username):
        request = str(request)  # 将 numpy.str_ 转换为普通的 Python 字符串
        self.request_counts[request] += 1  # 更新请求计数
        user_position = get_user_position(self.user_db_path, username)
        self.file_request_counts[request] += 1
        if user_position != (None, None):
            nearest_server = self.scheduler.get_next_server(user_position)
            if nearest_server is None:
                self.total_misses += 1
                return 0, False  # 无法找到最近的服务器，返回

            # 记录哪个服务器处理了请求
            server_index = self.servers.index(nearest_server)
            self.request_counts_by_server[server_index] += 1
            self.request_log.append(f"Request for {request} by {username} handled by Server {server_index + 1}")

            server_position = nearest_server.get_position()
            distance = self.scheduler.calculate_distance(server_position, user_position)
            simulated_response_time = self.calculate_response_time(distance)

            # 获取服务器响应，接收三个返回值
            response, found, cached = nearest_server.process_request(request)

            if found:
                if cached:
                    self.hit_counts_by_server[server_index] += 1
                    self.total_hits += 1
                    print(flush=True)
                    # print('simulated_response_time:', simulated_response_time, flush=True)
                    return simulated_response_time, True  # 缓存命中
                else:
                    # 未命中缓存，但在主服务器找到了文件
                    main_server_position = nearest_server.main_server.get_position()
                    server_to_main_distance = self.scheduler.calculate_distance(server_position, main_server_position)
                    main_server_response_time = self.calculate_response_time(server_to_main_distance)
                    total_response_time = simulated_response_time + main_server_response_time

                    # 直接调用 nearest_server 的 add_file 方法
                    nearest_server.add_file(request)
                    # print('total_response_time:', total_response_time, flush=True)
                    print(flush=True)
                    return total_response_time, False  # 未命中缓存但找到文件

            # 未找到文件的情况，记录未命中
            self.total_misses += 1
            return simulated_response_time, False  # 未命中，返回用户到节点的响应时间

        else:
            return 0, False  # 如果用户位置无效，返回0和未命中

    def simulate_requests(self, num_requests_per_user):
        total_response_time = 0
        user_response_times = []  # 用于存储每次请求的响应时间
        total_requests = len(self.user_requests) * num_requests_per_user

        # 重置统计数据
        self.user_response_times.clear()
        self.total_hits = 0
        self.total_requests = 0
        self.request_counts_by_server = {i: 0 for i in range(len(self.servers))}
        self.hit_counts_by_server = [0] * len(self.servers)

        for username, requests in self.user_requests.items():
            for i, request in enumerate(requests[:num_requests_per_user]):
                response_time, hit = self.send_request(request, username)
                total_response_time += response_time
                user_response_times.append(response_time)  # 记录每次请求的响应时间
                self.user_response_times.append([username, request, response_time])

        # 计算响应时间的标准差
        std_dev_response_time = calculate_response_time_std(user_response_times)

        self.total_requests = total_requests

        # 打印最终统计结果
        print(f"Total response time: {total_response_time:.2f}s")

        return total_response_time, std_dev_response_time


    def print_server_hit_rates(self):
        for i, server in enumerate(self.servers):
            total_requests = self.request_counts_by_server[i]
            hits = self.hit_counts_by_server[i]
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            # print(f"Server {i + 1} handled {total_requests} requests with a hit rate of {hit_rate:.2f}%")


def calculate_response_time_std(user_response_times):
    """计算用户响应时间的标准差"""
    if isinstance(user_response_times, dict):
        # 如果是字典格式，提取所有时间
        all_times = []
        for times in user_response_times.values():
            all_times.extend(times)
    else:
        # 如果是列表格式，直接使用它
        all_times = user_response_times

    n = len(all_times)
    if n > 1:
        mean = sum(all_times) / n
        variance = sum((x - mean) ** 2 for x in all_times) / n
        return math.sqrt(variance)
    else:
        return 0.0  # 如果只有一个或没有请求，则标准差为0
