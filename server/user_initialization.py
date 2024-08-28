import math
import os
import random
import sqlite3
import numpy as np


def initialize_users(user_db_path, num_users, grid_size):
    # initialize users' info
    initialize_user_database(user_db_path)
    fixed_users = []
    user_positions = generate_user_positions(num_users, grid_size)
    for i, position in enumerate(user_positions):
        username = f'user_{i + 1}'
        x, y = position
        add_user(user_db_path, username, x, y)
        fixed_users.append(username)
    return fixed_users, user_positions


def generate_user_positions(num_users, grid_size):
    # random position
    half_grid_size = grid_size // 2
    positions = [(random.uniform(-half_grid_size, half_grid_size), random.uniform(-half_grid_size, half_grid_size)) for
                 _ in range(num_users)]
    return positions


def initialize_user_database(user_db_path):
    # re-create user's db
    if os.path.exists(user_db_path):
        os.remove(user_db_path)
    conn = sqlite3.connect(user_db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE users (
                        username TEXT PRIMARY KEY,
                        x REAL,
                        y REAL)''')
    conn.commit()
    conn.close()


def add_user(user_db_path, username, x, y):
    conn = sqlite3.connect(user_db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, x, y) VALUES (?, ?, ?)', (username, x, y))
    conn.commit()
    conn.close()


def generate_zipf_distribution(num_files, s):
    # formular of Zipf distribution
    ranks = np.arange(1, num_files + 1)
    weights = 1 / np.power(ranks, s)
    weights /= weights.sum()
    return weights


def generate_user_requests_zipf(fixed_request_list, num_users, num_requests_per_user, zipf_s):
    # create requests for users by zipf
    num_files = len(fixed_request_list)
    weights = generate_zipf_distribution(num_files, s=zipf_s)

    user_requests = {}
    for i in range(num_users):
        requested_files = np.random.choice(fixed_request_list, size=num_requests_per_user, p=weights)
        user_requests[f'user_{i + 1}'] = list(requested_files)
    return user_requests


def generate_user_requests(fixed_request_list, num_users, num_requests_per_user):
    # create requests for users but all files have the same prob
    num_files = len(fixed_request_list)
    weights = np.ones(num_files) / num_files

    user_requests = {}
    for i in range(num_users):
        requested_files = np.random.choice(fixed_request_list, size=num_requests_per_user, replace=True, p=weights)
        user_requests[f'user_{i + 1}'] = list(requested_files)
    return user_requests
