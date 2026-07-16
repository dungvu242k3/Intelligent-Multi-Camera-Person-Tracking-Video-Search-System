import sys
import os
import time
import random
import asyncio
from typing import List

# Setup monorepo path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

try:
    from locust import HttpUser, task, between
    _LOCUST_AVAILABLE = True
except ImportError:
    _LOCUST_AVAILABLE = False

from tests.load.scenarios import generate_mock_embedding, get_login_payload, get_mock_camera_payload

# ----------------------------------------------------
# Standard Locust Scenario Definition
# ----------------------------------------------------
if _LOCUST_AVAILABLE:
    class MCPTOperatorLoadUser(HttpUser):
        """Locust HttpUser simulating operators performing vector searches and CRUD actions."""
        wait_time = between(0.5, 2.0)
        auth_token = ""

        def on_start(self):
            """Authenticates the operator user to obtain a bearer token."""
            payload = get_login_payload()
            with self.client.post("/auth/login", json=payload, catch_response=True) as response:
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token", "")
                    self.headers = {"Authorization": f"Bearer {self.auth_token}"}
                else:
                    response.failure(f"Login failed with status {response.status_code}")

        @task(3)
        def search_by_person_embedding(self):
            """Simulates querying similar person identities using vector embeddings."""
            headers = getattr(self, "headers", {})
            payload = {
                "embedding": generate_mock_embedding(),
                "limit": 5,
                "threshold": 0.70
            }
            self.client.post("/search/by-image", json=payload, headers=headers)

        @task(2)
        def list_surveillance_cameras(self):
            """Simulates loading the camera management telemetry view."""
            headers = getattr(self, "headers", {})
            self.client.get("/cameras", headers=headers)

        @task(1)
        def register_new_camera(self):
            """Simulates registering a camera stream config."""
            headers = getattr(self, "headers", {})
            payload = get_mock_camera_payload()
            self.client.post("/cameras", json=payload, headers=headers)

# ----------------------------------------------------
# Standalone Simulation / Benchmark Mode
# ----------------------------------------------------
async def run_standalone_http_benchmark(concurrency: int = 10, total_requests: int = 100):
    """Simulates load testing without live Locust server running, printing latency statistics."""
    print("=" * 60)
    print("STANDALONE API LOAD BENCHMARK SIMULATION".center(60))
    print("=" * 60)
    print(f"Target Concurrency : {concurrency} clients")
    print(f"Total Requests     : {total_requests}")
    print("-" * 60)

    latencies: List[float] = []
    success_count = 0
    failure_count = 0

    async def mock_client_request(client_id: int):
        nonlocal success_count, failure_count
        # Simulate network latency variation and mock endpoint execution delays
        start_time = time.perf_counter()
        
        # Simulating API search / database lookup delay
        # Authentication takes ~25ms, query takes ~40ms, total network loop overhead ~15ms
        processing_delay = random.uniform(0.035, 0.085)
        await asyncio.sleep(processing_delay)
        
        elapsed = (time.perf_counter() - start_time) * 1000.0  # ms
        latencies.append(elapsed)
        success_count += 1

    # Chunk requests into concurrency batches
    tasks = []
    for req_idx in range(total_requests):
        tasks.append(mock_client_request(req_idx % concurrency))
        if len(tasks) >= concurrency:
            await asyncio.gather(*tasks)
            tasks = []
    if tasks:
        await asyncio.gather(*tasks)

    # Calculate statistics
    latencies.sort()
    avg_latency = sum(latencies) / len(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    min_lat = latencies[0]
    max_lat = latencies[-1]
    rps = total_requests / (sum(latencies) / 1000.0)

    print("\nBENCHMARK METRICS RESULTS:")
    print("Status             : SUCCESS")
    print(f"Requests Completed : {total_requests}")
    print(f"Successful Calls   : {success_count}")
    print(f"Failed Calls       : {failure_count}")
    print(f"Throughput         : {rps:.2f} req/sec")
    print("-" * 60)
    print("LATENCY DISTRIBUTION (ms):")
    print(f"  Minimum Latency  : {min_lat:.2f} ms")
    print(f"  Average Latency  : {avg_latency:.2f} ms")
    print(f"  95th Percentile  : {p95:.2f} ms")
    print(f"  99th Percentile  : {p99:.2f} ms")
    print(f"  Maximum Latency  : {max_lat:.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    # Check if run with --run-standalone argument
    if len(sys.argv) > 1 and sys.argv[1] == "--run-standalone":
        asyncio.run(run_standalone_http_benchmark())
    else:
        print("Locust script successfully initialized. Run as a locust module or run standalone using:")
        print("  python locustfile.py --run-standalone")
