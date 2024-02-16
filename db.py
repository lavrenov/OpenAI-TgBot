import sqlite3
import threading

db_name = "main.db"
lock = threading.Lock()
thread_local = threading.local()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def connect():
    if not hasattr(thread_local, "conn"):
        conn = sqlite3.connect(db_name)
        conn.row_factory = dict_factory
        thread_local.conn = conn

    return thread_local.conn


def close():
    conn = getattr(thread_local, "conn", None)
    if conn is not None:
        conn.close()


def init():
    with connect() as conn:
        cur = conn.cursor()

        cur.execute("CREATE TABLE IF NOT EXISTS messages ("
                    "id INTEGER PRIMARY KEY, "
                    "user_id INTEGER, "
                    "role TEXT, "
                    "content TEXT, "
                    "date DATETIME"
                    ")")

        conn.commit()


def update_record(table, data, unique_cols):
    with connect() as conn:
        cursor = conn.cursor()

        keys = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())

        where = {key: str(values[index]) for index, key in enumerate(data) if key in unique_cols}
        row = get_rows(table, where, True)
        row_id = row["id"] if row else 0
        if row_id:
            sql = (f"UPDATE {table} SET {', '.join([f'{key}=?' for key in data.keys()])} "
                   f"WHERE {' AND '.join([f'{key}=?' for key in where.keys()])}")
            values += tuple(where.values())
        else:
            sql = f"INSERT INTO {table} ({keys}) VALUES ({placeholders})"

        cursor.execute(sql, values)
        row_id = row_id if row_id else cursor.lastrowid
        conn.commit()

    return row_id


def get_rows(table, where=None, one=False) -> list or dict:
    if where is None:
        where = {}
    with connect() as conn:
        cursor = conn.cursor()
        values = tuple(where.values())

        sql = f"SELECT * FROM {table}"
        sql += f" WHERE {' AND '.join([f'{key}=?' for key in where.keys()])}" if len(where) else ""

        cursor.execute(sql, values)
        rows = cursor.fetchone() if one else cursor.fetchall()

    return rows
