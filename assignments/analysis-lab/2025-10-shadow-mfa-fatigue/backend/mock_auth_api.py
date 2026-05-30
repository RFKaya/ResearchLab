from flask import Flask, request, jsonify
import logging
import random
import time

app = Flask(__name__)

# Basic logging setup to stdout
logging.basicConfig(level=logging.INFO, format='{"timestamp": %(created)f, "client_ip": "%(message)s"}') # Custom format will be handled in route

@app.route('/api/v1/auth/mfa/trigger', methods=['POST'])
def trigger_mfa():
    """
    Simulates a legacy MFA trigger endpoint.
    It takes a username and sends a simulated push.
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', 'unknown_user')
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    
    # Simulate processing delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Log the event (this log structure is what mfa_fatigue_detector.py expects)
    log_entry = {
        "timestamp": int(time.time()),
        "username": username,
        "event": "mfa_push",
        "status": "pending",
        "client_ip": client_ip
    }
    
    # Write to a file that the detector can read (simulate shared volume in docker)
    with open('/var/log/auth_mfa_events.log', 'a') as f:
        import json
        f.write(json.dumps(log_entry) + '\n')

    print(json.dumps(log_entry)) # Also print to console for docker logs

    return jsonify({"status": "success", "message": "Push notification sent.", "user": username}), 200

@app.route('/api/v1/auth/mfa/verify', methods=['POST'])
def verify_mfa():
    """
    Simulates checking if the user approved the push.
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', 'unknown_user')
    client_ip = request.headers.get('X-Real-IP', request.remote_addr)
    
    # For simulation, read from request or fallback to random choice
    status = data.get('status', random.choice(["success", "denied"]))
    
    log_entry = {
        "timestamp": int(time.time()),
        "username": username,
        "event": "mfa_push",
        "status": status,
        "client_ip": client_ip
    }
    
    with open('/var/log/auth_mfa_events.log', 'a') as f:
        import json
        f.write(json.dumps(log_entry) + '\n')
        
    print(json.dumps(log_entry))
    
    if status == "success":
        return jsonify({"status": "success", "message": "Authentication successful"}), 200
    else:
        return jsonify({"status": "error", "message": "Authentication denied"}), 401

if __name__ == '__main__':
    # Listen on all interfaces so NGINX can proxy to it
    app.run(host='0.0.0.0', port=8080)
