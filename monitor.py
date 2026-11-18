
import requests
import time
from datetime import datetime
from database import save_check


# Websites to monitor
websites = [
    "https://example.com",
    "https://google.com",
    "https://github.com"
]

# Check interval in seconds
CHECK_INTERVAL = 60


def check_server(url):

    print("\nChecking:", url)

    start_time = time.time()

    status_code = None
    response_time = None
    error = None

    try:
        response = requests.get(url, timeout=5)

        end_time = time.time()

        response_time = round(
            (end_time - start_time) * 1000, 2
        )

        status_code = response.status_code

        if status_code < 400:
            status = "UP"
        else:
            status = "DOWN"

        print("Status:", status)
        print("Status Code:", status_code)
        print("Response Time:", response_time, "ms")

    except requests.RequestException as e:

        status = "DOWN"
        error = str(e)

        print("Status:", status)
        print("Error:", error)

    checked_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    save_check(
        url,
        status,
        status_code,
        response_time,
        checked_at,
        error
    )

    print("Checked At:", checked_at)
    print("Log saved successfully!")


# Automatic monitoring

print("SERVER UPTIME MONITORING SYSTEM")
print("Monitoring Started...")
print("Press CTRL + C to stop monitoring.")

try:

    while True:

        print("\n========== NEW MONITORING CYCLE ==========")

        for website in websites:
            check_server(website)

        print("\nNext check after", CHECK_INTERVAL, "seconds.")

        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:

    print("\nMonitoring stopped by user.")
