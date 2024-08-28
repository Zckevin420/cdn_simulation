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
        self.scheduler = scheduler
        self.user_requests = user_requests or {}
        self.request_counts = {str(filename): 0 for filename in request_list}
        self.user_response_times = []  # store response time
        self.total_hits = 0
        self.total_requests = 0
        self.total_misses = 0
        self.request_counts_by_server = {i: 0 for i in range(len(servers))}  # counter
        self.hit_counts_by_server = [0] * len(servers)
        self.file_request_counts = Counter()

        if scheduler == 'nearest':
            self.scheduler = NearestServerScheduler(servers)
        elif scheduler == 'round_robin':
            self.scheduler = RoundRobinScheduler(servers)
        elif scheduler == 'distance_round_robin':
            self.scheduler = DistanceRoundRobinScheduler(servers)
        else:
            print('no scheduler')
            return

    def calculate_response_time(self, distance):
        # calc time by distance
        return 2 * ((distance // 1000) + (distance % 1000) / 1000.0)

    def send_request(self, request, username):
        request = str(request)
        self.request_counts[request] += 1
        user_position = get_user_position(self.user_db_path, username)
        self.file_request_counts[request] += 1
        if user_position != (None, None):
            nearest_server = self.scheduler.get_next_server(user_position)
            if nearest_server is None:
                self.total_misses += 1
                return 0, False

            # counts which server gets a request
            server_index = self.servers.index(nearest_server)
            self.request_counts_by_server[server_index] += 1

            server_position = nearest_server.get_position()
            distance = self.scheduler.calculate_distance(server_position, user_position)
            simulated_response_time = self.calculate_response_time(distance)

            response, found, cached = nearest_server.process_request(request)

            if found:
                if cached:
                    # find in the node
                    self.hit_counts_by_server[server_index] += 1
                    self.total_hits += 1
                    print(flush=True)
                    # print('simulated_response_time:', simulated_response_time, flush=True)
                    return simulated_response_time, True
                else:
                    # not in node but in main
                    main_server_position = nearest_server.main_server.get_position()
                    server_to_main_distance = self.scheduler.calculate_distance(server_position, main_server_position)
                    main_server_response_time = self.calculate_response_time(server_to_main_distance)
                    total_response_time = simulated_response_time + main_server_response_time

                    # give file to the node
                    nearest_server.add_file(request)
                    # print('total_response_time:', total_response_time, flush=True)
                    print(flush=True)
                    return total_response_time, False

            # not found
            self.total_misses += 1
            return simulated_response_time, False

        else:
            return 0, False

    def simulate_requests(self, num_requests_per_user):
        total_response_time = 0
        user_response_times = []  # store every response time
        total_requests = len(self.user_requests) * num_requests_per_user

        # initial all data
        self.user_response_times.clear()
        self.total_hits = 0
        self.total_requests = 0
        self.request_counts_by_server = {i: 0 for i in range(len(self.servers))}
        self.hit_counts_by_server = [0] * len(self.servers)

        for username, requests in self.user_requests.items():
            for i, request in enumerate(requests[:num_requests_per_user]):
                response_time, hit = self.send_request(request, username)
                total_response_time += response_time
                user_response_times.append(response_time)
                self.user_response_times.append([username, request, response_time])

        std_dev_response_time = calculate_response_time_std(user_response_times)

        self.total_requests = total_requests

        print(f"Total response time: {total_response_time:.2f}s")

        return total_response_time, std_dev_response_time

    # def print_server_hit_rates(self):
    #     for i, server in enumerate(self.servers):
    #         total_requests = self.request_counts_by_server[i]
    #         hits = self.hit_counts_by_server[i]
    #         hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
    #         # print(f"Server {i + 1} handled {total_requests} requests with a hit rate of {hit_rate:.2f}%")


def calculate_response_time_std(user_response_times):
    if isinstance(user_response_times, dict):
        all_times = []
        for times in user_response_times.values():
            all_times.extend(times)
    else:
        all_times = user_response_times

    n = len(all_times)
    if n > 1:
        mean = sum(all_times) / n
        variance = sum((x - mean) ** 2 for x in all_times) / n
        return math.sqrt(variance)
    else:
        return 0.0
