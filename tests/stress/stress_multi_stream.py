import sys
import os
import time
import uuid
import random
import asyncio
import argparse
from typing import List
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

# Setup path to import packages correctly in monorepo
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

# Mock cv2 before importing any GStreamer or probe callback code
sys.modules['cv2'] = MagicMock()

from application.use_cases.process_tracking_event import ProcessTrackingEventUseCase  # noqa: E402
from packages.domain.entities.person import Person  # noqa: E402

class StressTestRunner:
    """Stress test runner simulating high-throughput camera telemetry events ingestion."""
    def __init__(self, streams_count: int, duration_seconds: int):
        self.streams_count = streams_count
        self.duration_seconds = duration_seconds
        
        # Performance trackers
        self.total_processed = 0
        self.latencies: List[float] = []
        self.failures_count = 0
        
        # Mocks for clean architecture boundaries
        self.mock_person_repo = AsyncMock()
        self.mock_tracking_repo = AsyncMock()
        self.mock_vector_store = AsyncMock()
        self.mock_kafka_producer = MagicMock()
        
        # Preset mocks to simulate 80% ReID matching rates and fast SQL writes
        self.person_id = uuid.uuid4()
        self.mock_vector_store.search_similar.return_value = [
            {"person_id": self.person_id, "score": 0.88}
        ]
        self.mock_person_repo.get_by_id.return_value = Person(
            id=self.person_id,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )

        self.usecase = ProcessTrackingEventUseCase(
            person_repo=self.mock_person_repo,
            tracking_repo=self.mock_tracking_repo,
            vector_store=self.mock_vector_store,
            kafka_producer=self.mock_kafka_producer
        )

    async def simulate_camera_stream(self, camera_id: uuid.UUID):
        """Simulates a camera feed producing telemetry frames at ~30 FPS."""
        frame_number = 0
        end_time = time.perf_counter() + self.duration_seconds
        
        while time.perf_counter() < end_time:
            # DeepStream event structure payload
            event_data = {
                "event_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "camera_id": str(camera_id),
                "frame_number": frame_number,
                "detection": {
                    "type": "person",
                    "confidence": random.uniform(0.75, 0.99),
                    "bbox": {
                        "left": random.uniform(10.0, 100.0),
                        "top": random.uniform(10.0, 100.0),
                        "width": random.uniform(30.0, 80.0),
                        "height": random.uniform(100.0, 200.0)
                    },
                    "embedding": [random.uniform(-0.5, 0.5) for _ in range(512)],
                    "crop_path": f"crops/{camera_id}/frame_{frame_number}.jpg"
                }
            }
            
            # Execute pipeline usecase
            start_process = time.perf_counter()
            try:
                await self.usecase.execute(event_data)
                processing_time = (time.perf_counter() - start_process) * 1000.0 # ms
                self.latencies.append(processing_time)
                self.total_processed += 1
            except Exception:
                self.failures_count += 1
                
            frame_number += 1
            
            # 30 FPS target = ~33.3ms delay between frames.
            # We subtract processing latency to keep frequency steady.
            sleep_duration = max(0.001, 0.033 - (time.perf_counter() - start_process))
            await asyncio.sleep(sleep_duration)

    async def run(self):
        print("=" * 60)
        print("AI PIPELINE MULTI-STREAM STRESS TEST".center(60))
        print("=" * 60)
        print(f"Simulating Streams : {self.streams_count} cameras (each at 30 FPS)")
        print(f"Run Duration       : {self.duration_seconds} seconds")
        print(f"Expected Throughput: {self.streams_count * 30} events/sec")
        print("-" * 60)
        print("Simulating ingestion telemetry loops...")

        start_time = time.perf_counter()
        
        # Spawn stream loops
        tasks = []
        for _ in range(self.streams_count):
            camera_uuid = uuid.uuid4()
            tasks.append(self.simulate_camera_stream(camera_uuid))
            
        await asyncio.gather(*tasks)
        
        elapsed_seconds = time.perf_counter() - start_time
        
        # Calculate statistics
        if self.latencies:
            self.latencies.sort()
            avg_lat = sum(self.latencies) / len(self.latencies)
            p95 = self.latencies[int(len(self.latencies) * 0.95)]
            p99 = self.latencies[int(len(self.latencies) * 0.99)]
            min_lat = self.latencies[0]
            max_lat = self.latencies[-1]
            actual_throughput = self.total_processed / elapsed_seconds
        else:
            avg_lat = p95 = p99 = min_lat = max_lat = actual_throughput = 0.0

        print("\nSTRESS TEST METRICS RESULTS:")
        print(f"Total Simulation Time : {elapsed_seconds:.2f} seconds")
        print(f"Events Ingested       : {self.total_processed} frames")
        print(f"Ingestion Failures    : {self.failures_count}")
        print(f"Actual Throughput     : {actual_throughput:.2f} frames/sec")
        print("-" * 60)
        print("PIPELINE INGESTION LATENCY (ms):")
        print(f"  Minimum Delay       : {min_lat:.2f} ms")
        print(f"  Average Delay       : {avg_lat:.2f} ms")
        print(f"  95th Percentile     : {p95:.2f} ms")
        print(f"  99th Percentile     : {p99:.2f} ms")
        print(f"  Maximum Delay       : {max_lat:.2f} ms")
        print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Camera Ingestion Pipeline Stress Simulator")
    parser.add_argument("--streams", type=int, default=10, help="Number of simulated cameras (default: 10)")
    parser.add_argument("--duration", type=int, default=5, help="Simulation duration in seconds (default: 5)")
    
    args = parser.parse_args()
    
    asyncio.run(StressTestRunner(args.streams, args.duration).run())
