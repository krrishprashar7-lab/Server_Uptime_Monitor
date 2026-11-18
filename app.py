
from flask import Flask, render_template
import sqlite3
import os

from ml_anomaly import get_anomaly_report

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "server_logs.db")


def get_dashboard_data():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            website,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS up,
            AVG(response_time) AS avg_response
        FROM server_logs
        GROUP BY website
    """)

    summaries = [dict(row) for row in cursor.fetchall()]

    for item in summaries:

        cursor.execute("""
            SELECT status
            FROM server_logs
            WHERE website = ?
            ORDER BY id DESC
            LIMIT 1
        """, (item["website"],))

        latest = cursor.fetchone()

        item["current_status"] = (
            latest["status"] if latest else "UNKNOWN"
        )

        item["uptime"] = round(
            item["up"] / item["total"] * 100, 2
        ) if item["total"] else 0

    cursor.execute("SELECT COUNT(*) FROM server_logs")
    total_checks = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'UP' THEN 1 ELSE 0 END) AS up
        FROM server_logs
    """)

    result = cursor.fetchone()

    overall_uptime = (
        round((result["up"] or 0) / result["total"] * 100, 2)
        if result["total"] else 0
    )

    cursor.execute("""
        SELECT *
        FROM server_logs
        ORDER BY id DESC
        LIMIT 20
    """)

    logs = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return summaries, logs, total_checks, overall_uptime


@app.route("/")
def dashboard():

    summaries, logs, total_checks, overall_uptime = (
        get_dashboard_data()
    )

    ml_report = get_anomaly_report()

    # Add ML baseline to each website summary
    baselines = ml_report.get("website_baselines", {})

    for item in summaries:

        baseline = baselines.get(item["website"])

        item["ml_baseline"] = (
            round(baseline, 2)
            if baseline is not None else None
        )

    # Add severity to anomaly details
    for anomaly in ml_report.get("anomalies", []):

        if anomaly["reason"] == "SERVER DOWN":
            anomaly["severity"] = "CRITICAL"

        elif anomaly["reason"] == "UNUSUAL RESPONSE TIME":
            anomaly["severity"] = "WARNING"

        else:
            anomaly["severity"] = "INFO"

    return render_template(
        "index.html",
        summaries=summaries,
        logs=logs,
        total_checks=total_checks,
        overall_uptime=overall_uptime,
        ml_report=ml_report
    )


if __name__ == "__main__":
    app.run(debug=True)
