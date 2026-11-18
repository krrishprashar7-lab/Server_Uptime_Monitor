
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "server_logs.db")


def generate_report():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            website,
            COUNT(*) AS total_checks,
            SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END)
            AS up_checks,
            AVG(response_time) AS avg_response
        FROM server_logs
        GROUP BY website
    """)

    records = cursor.fetchall()

    print("\n========== UPTIME REPORT ==========")

    for website, total, up, avg_response in records:

        uptime = (up / total) * 100

        print("\nWebsite:", website)
        print("Total Checks:", total)
        print("Successful Checks:", up)
        print("Uptime:", round(uptime, 2), "%")

        if avg_response is not None:
            print("Average Response:",
                  round(avg_response, 2), "ms")

        print("-----------------------------------")

    conn.close()


generate_report()
