#!/usr/bin/env python3
import os
import time
import requests
from collections import deque
from datetime import datetime

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ERROR_RATE_THRESHOLD = 2.0
WINDOW_SIZE = 200
ALERT_COOLDOWN_SEC = 60

last_pool = None
request_window = deque(maxlen=WINDOW_SIZE)
last_alert_time = {'failover': 0, 'error_rate': 0}

def send_slack(message, alert_type):
    global last_alert_time
    current_time = time.time()
    if current_time - last_alert_time.get(alert_type, 0) < ALERT_COOLDOWN_SEC:
        return
    payload = {"text": f"🚨 *HNG Alert* 🚨\n\n{message}"}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        last_alert_time[alert_type] = current_time
        print(f"[ALERT] {alert_type}")
    except:
        pass

def check_pool():
    global last_pool
    import subprocess
    result = subprocess.run(['curl', '-s', '-i', 'http://nginx:80/version'], 
                          capture_output=True, text=True, timeout=2)
    if 'X-App-Pool:' in result.stdout:
        for line in result.stdout.split('\n'):
            if 'X-App-Pool:' in line:
                pool = line.split(':')[1].strip()
                if last_pool and pool != last_pool:
                    msg = f"*Failover!*\n{last_pool} → {pool}\nTime: {datetime.now()}"
                    send_slack(msg, 'failover')
                last_pool = pool
                return pool
    return None

print("[WATCHER] Starting...")
time.sleep(5)
while True:
    try:
        check_pool()
        time.sleep(2)
    except:
        pass
