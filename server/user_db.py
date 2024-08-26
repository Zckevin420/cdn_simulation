import sqlite3

def initialize_user_database(db_path): # 初始化用户数据库，创建用户表
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_user(db_path, username, x, y): # 向用户数据库添加用户记录（如果用户不存在）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (username, x, y) VALUES (?, ?, ?)', (username, x, y))
    conn.commit()
    conn.close()


def get_user_position(db_path, username): # 根据用户名获取用户位置
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT x, y FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return (result[0], result[1]) if result else (None, None)
