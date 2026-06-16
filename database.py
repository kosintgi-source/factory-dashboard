import sqlite3
def get_conn():
    return sqlite3.connect('database/factory.db', check_same_thread=False)
