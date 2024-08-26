import matplotlib.pyplot as plt

def plot_positions(user_positions, server_positions, user_server_connections, filename="positions.png"):
    """绘制用户和服务器的位置图，并绘制用户与选择服务器之间的连线，最后保存为图片"""
    # for idx, (user_pos, server_idx) in enumerate(user_server_connections):
    #     print(f"User {idx + 1} at {user_pos} is connected to Server {server_idx + 1} at {server_positions[server_idx]}")

    user_x, user_y = zip(*user_positions)
    server_x, server_y = zip(*server_positions)

    plt.figure(figsize=(10, 8))

    # 绘制用户与其对应的服务器之间的连线
    for user_pos, server_index in user_server_connections:
        server_pos = server_positions[server_index]
        plt.plot([user_pos[0], server_pos[0]], [user_pos[1], server_pos[1]], color='gray', linewidth=0.5)

    # 绘制用户和服务器的位置
    plt.scatter(user_x, user_y, c='blue', label='Users', marker='o', s=1)
    plt.scatter(server_x, server_y, c='red', label='Servers', marker='^', s=50)
    plt.scatter(0, 0, c='green', label='Main Server', marker='s', s=80)  # 主服务器在原点

    plt.xlabel('X Position')
    plt.ylabel('Y Position')
    plt.title('User and Server Positions')
    plt.legend()
    plt.grid(True)
    plt.savefig(filename)
    plt.close()


