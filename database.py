
import sqlite3
import os

# Database folder and file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FOLDER = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(LOG_FOLDER, "server_logs.db")


def create_database():

    os.makedirs(LOG_FOLDER, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website TEXT,
            status TEXT,
            status_code INTEGER,
            response_time REAL,
            checked_at TEXT,
            error TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_check(website, status, status_code,
               response_time, checked_at, error=None):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO server_logs
        (website, status, status_code,
         response_time, checked_at, error)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (website, status, status_code,
          response_time, checked_at, error))

    conn.commit()
    conn.close()


create_database()
