
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "server_logs.db")


def view_logs():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, website, status, status_code,
               response_time, checked_at
        FROM server_logs
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    print("\n========== SERVER MONITORING HISTORY ==========")

    if not records:
        print("No monitoring records found.")

    else:
        for record in records:
            print("\nLog ID:", record[0])
            print("Website:", record[1])
            print("Status:", record[2])
            print("Status Code:", record[3])
            print("Response Time:", record[4], "ms")
            print("Checked At:", record[5])
            print("------------------------------------------")

    print("\nTotal Records:", len(records))

    conn.close()


view_logs()
