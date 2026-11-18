
import sqlite3
import os
import math
from statistics import median
from collections import defaultdict
from sklearn.ensemble import IsolationForest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "server_logs.db")

MIN_RECORDS = 10
CONTAMINATION = 0.05
TRAIN_RATIO = 0.70


def get_baselines(records):
    """Calculate website-wise response-time baselines."""

    website_groups = defaultdict(list)

    for row in records:
        website_groups[row[0]].append(float(row[2]))

    baselines = {}

    for website, values in website_groups.items():
        baselines[website] = median(values)

    return website_groups, baselines


def create_features(records, website_groups, website_baselines):
    """Create response-time features for Isolation Forest."""

    features = []

    for row in records:
        website = row[0]
        response_time = float(row[2])

        baseline = website_baselines.get(website, 1)

        values = website_groups.get(website, [baseline])

        deviations = [
            abs(value - baseline)
            for value in values
        ]

        mad = median(deviations)

        scale = max(
            1.4826 * mad,
            baseline * 0.05,
            1
        )

        ratio = response_time / max(baseline, 1)
        robust_z = (response_time - baseline) / scale

        features.append([ratio, robust_z])

    return features


def evaluate_model(valid_records):
    """
    Train on the first 70% of records.
    Test on the remaining 30%.
    """

    total = len(valid_records)

    if total < MIN_RECORDS:
        return {
            "training_records": 0,
            "testing_records": 0,
            "test_anomalies": 0,
            "test_anomaly_rate": 0,
            "note": "Not enough records for model evaluation."
        }

    split_index = int(total * TRAIN_RATIO)

    train_records = valid_records[:split_index]
    test_records = valid_records[split_index:]

    if len(train_records) < 5 or len(test_records) == 0:
        return {
            "training_records": len(train_records),
            "testing_records": len(test_records),
            "test_anomalies": 0,
            "test_anomaly_rate": 0,
            "note": "Not enough training or testing records."
        }

    # Calculate baselines using training records only.
    train_groups, train_baselines = get_baselines(train_records)

    # Create separate training and testing features.
    train_features = create_features(
        train_records,
        train_groups,
        train_baselines
    )

    test_features = create_features(
        test_records,
        train_groups,
        train_baselines
    )

    # Train the model on earlier records.
    evaluation_model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=42
    )

    evaluation_model.fit(train_features)

    # Test on later, unseen records.
    predictions = evaluation_model.predict(test_features)

    test_anomalies = sum(
        1 for prediction in predictions
        if prediction == -1
    )

    anomaly_rate = round(
        (test_anomalies / len(test_records)) * 100,
        2
    )

    return {
        "training_records": len(train_records),
        "testing_records": len(test_records),
        "test_anomalies": test_anomalies,
        "test_anomaly_rate": anomaly_rate,
        "note": (
            "Evaluation completed using chronological "
            "70% training and 30% testing data. "
            "Anomaly rate is not model accuracy."
        )
    }


def get_anomaly_report():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT website, status, response_time, checked_at
        FROM server_logs
        ORDER BY id ASC
    """)

    records = cursor.fetchall()
    conn.close()

    valid_records = []

    for row in records:
        try:
            response_time = float(row[2])

            if (
                row[1] == "UP"
                and math.isfinite(response_time)
                and response_time >= 0
            ):
                valid_records.append(row)

        except (TypeError, ValueError):
            continue

    down_records = [
        row for row in records
        if row[1] != "UP"
    ]

    anomalies = []

    # Server DOWN alerts
    for row in down_records:
        anomalies.append({
            "website": row[0],
            "status": row[1],
            "response_time": row[2],
            "checked_at": row[3],
            "reason": "SERVER DOWN"
        })

    average = 0
    median_time = 0
    website_baselines = {}

    note = "Insufficient data for ML analysis."

    evaluation = {
        "training_records": 0,
        "testing_records": 0,
        "test_anomalies": 0,
        "test_anomaly_rate": 0,
        "note": "Not enough records for model evaluation."
    }

    if valid_records:

        times = [
            float(row[2])
            for row in valid_records
        ]

        average = round(sum(times) / len(times), 2)
        median_time = round(median(times), 2)

        website_groups, website_baselines = get_baselines(
            valid_records
        )

        website_baselines = {
            website: round(baseline, 2)
            for website, baseline in website_baselines.items()
        }

    # Main Isolation Forest anomaly detection
    if len(valid_records) >= MIN_RECORDS:

        website_groups, full_baselines = get_baselines(
            valid_records
        )

        features = create_features(
            valid_records,
            website_groups,
            full_baselines
        )

        model = IsolationForest(
            n_estimators=200,
            contamination=CONTAMINATION,
            random_state=42
        )

        model.fit(features)

        predictions = model.predict(features)
        scores = model.decision_function(features)

        for row, prediction, score in zip(
            valid_records,
            predictions,
            scores
        ):

            if prediction == -1:

                anomalies.append({
                    "website": row[0],
                    "status": row[1],
                    "response_time": round(float(row[2]), 2),
                    "checked_at": row[3],
                    "reason": "UNUSUAL RESPONSE TIME",
                    "anomaly_score": round(float(score), 4)
                })

        note = (
            "Website-wise Isolation Forest ML analysis completed."
        )

        # Separate chronological model evaluation
        evaluation = evaluate_model(valid_records)

    return {
        "total_records": len(records),
        "successful_checks": len(valid_records),
        "down_alerts": len(down_records),
        "anomaly_count": len(anomalies),
        "average_response": average,
        "median_response": median_time,
        "anomalies": anomalies,
        "website_baselines": website_baselines,
        "model_name": "Isolation Forest",
        "ml_ready": len(valid_records) >= MIN_RECORDS,
        "note": note,
        "evaluation": evaluation
    }


if __name__ == "__main__":

    report = get_anomaly_report()

    print("\n===================================")
    print(" MACHINE LEARNING ANOMALY REPORT")
    print("===================================")

    print("Total Records:", report["total_records"])
    print("Successful Checks:", report["successful_checks"])
    print("Server DOWN Alerts:", report["down_alerts"])
    print("Detected Anomalies:", report["anomaly_count"])
    print("Average Response:", report["average_response"], "ms")
    print("Median Response:", report["median_response"], "ms")

    print("\nWebsite-wise Baselines:")

    for website, baseline in report["website_baselines"].items():
        print(website, ":", baseline, "ms")

    print("\nML Status:", report["note"])

    print("\n========== MODEL EVALUATION ==========")

    evaluation = report["evaluation"]

    print("Training Records:", evaluation["training_records"])
    print("Testing Records:", evaluation["testing_records"])
    print("Test Anomalies:", evaluation["test_anomalies"])
    print("Test Anomaly Rate:", evaluation["test_anomaly_rate"], "%")
    print("Evaluation Note:", evaluation["note"])

    print("\n========== ANOMALY DETAILS ==========")

    for item in report["anomalies"]:

        print("\nWebsite:", item["website"])
        print("Status:", item["status"])
        print("Response:", item["response_time"], "ms")
        print("Alert:", item["reason"])

        if "anomaly_score" in item:
            print("Anomaly Score:", item["anomaly_score"])

        print("Checked At:", item["checked_at"])

    print("\nMachine Learning Analysis Completed!")
