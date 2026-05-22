#!/usr/bin/env python3
import json
import time
from collections import defaultdict, deque
import sys
import os

# Path to the authentication log file
LOG_FILE_PATH = "/var/log/auth_mfa_events.log"

# Detection threshold criteria
TIME_WINDOW_SEC = 60         # Rolling window interval in seconds
THRESHOLD_PUSH_ATTEMPTS = 5   # Number of failed/pending prompts before success that flags a warning

# In-memory storage for user authentication requests
# Format: { username: deque([(timestamp, event_type, status), ...]) }
user_history = defaultdict(deque)

def process_log_line(line):
    """
    Parses and evaluates a single log entry.
    Expected JSON schema:
    {"timestamp": 1716382000, "username": "ahmet.yilmaz", "event": "mfa_push", "status": "pending"}
    """
    try:
        log_data = json.loads(line.strip())
        current_time = log_data["timestamp"]
        username = log_data["username"]
        event = log_data["event"]
        status = log_data["status"]
    except (json.JSONDecodeError, KeyError, TypeError):
        # Ignore malformed or irrelevant logs
        return

    history = user_history[username]

    # Purge logs outside the rolling window
    while history and (current_time - history[0][0]) > TIME_WINDOW_SEC:
        history.popleft()

    # Append current authentication attempt
    history.append((current_time, event, status))

    # Evaluate pattern upon a successful authentication
    if event == "mfa_push" and status == "success":
        # Filter out preceding non-successful push notifications in the window
        push_attempts = [e for e in history if e[1] == "mfa_push" and e[2] in ("pending", "denied")]
        
        if len(push_attempts) >= THRESHOLD_PUSH_ATTEMPTS:
            time_difference = current_time - push_attempts[0][0]
            print(f"[!] ALERT: Suspicious Shadow MFA Fatigue Detected!")
            print(f"    Target User   : {username}")
            print(f"    Time Interval : {time_difference} seconds")
            print(f"    Push Spams    : {len(push_attempts)} failed prompts followed by a successful bypass")
            print(f"    First Push At : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(push_attempts[0][0]))}")
            print(f"    Authorized At : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_time))}")
            print("-" * 65)

def main():
    print("[*] Real-time Shadow MFA Fatigue log analyzer started...")
    print(f"[*] Monitoring log file: {LOG_FILE_PATH}")
    
    if not os.path.exists(LOG_FILE_PATH):
        print(f"[WARNING] Log file does not exist yet. Creating a blank file at: {LOG_FILE_PATH}")
        try:
            os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
            with open(LOG_FILE_PATH, "a") as f:
                pass
        except Exception as e:
            print(f"[ERROR] Failed to initialize log file: {e}")
            sys.exit(1)

    # Continuously read the log file (equivalent to tail -f)
    try:
        with open(LOG_FILE_PATH, "r") as f:
            # Go to the end of the file
            f.seek(0, 2)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                process_log_line(line)
    except KeyboardInterrupt:
        print("\n[*] Exiting log analyzer...")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
