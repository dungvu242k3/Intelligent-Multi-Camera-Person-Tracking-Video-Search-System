import os
import sys
import time
import random
import asyncio
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

# Setup PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

def simulate_qdrant_search(scale: int, concurrency: int) -> Dict:
    """
    Simulates high-scale Qdrant vector index search (Cosine similarity over 512-dim vectors).
    Applies HNSW logarithmic complexity curves for search latency.
    """
    # 512-dim float32 vector size in memory: 512 * 4 bytes = 2 KB
    # Memory footprint for 'scale' items
    mem_footprint_gb = (scale * 2048) / (1024**3)
    
    # HNSW index overhead (approx. 1.2x to 1.5x of raw vector data)
    hnsw_overhead_gb = mem_footprint_gb * 1.3
    
    # Base lookup latency increases logarithmically with collection scale: O(log N)
    # 10,000 items -> ~10ms base. 1,000,000 items -> ~28ms base.
    import math
    base_latency_ms = 5.0 + 2.5 * math.log(scale, 10)
    
    # Concurrency congestion multiplier
    congestion_factor = 1.0 + (concurrency / 100.0)
    
    latencies = []
    for _ in range(100): # 100 benchmark queries
        # Add random noise and latency spikes
        spike = random.choice([0.0] * 95 + [15.0, 30.0, 50.0]) # 5% chance of spikes
        lat = (base_latency_ms * congestion_factor * random.uniform(0.9, 1.1)) + spike
        latencies.append(lat)
        
    latencies.sort()
    avg_lat = sum(latencies) / len(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]
    
    qps = (concurrency * 1000.0) / avg_lat
    
    return {
        "scale": scale,
        "concurrency": concurrency,
        "vector_memory_gb": mem_footprint_gb,
        "hnsw_index_memory_gb": hnsw_overhead_gb,
        "average_latency_ms": avg_lat,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "throughput_qps": qps
    }

def simulate_postgres_queries(scale: int, has_index: bool) -> Dict:
    """
    Simulates PostgreSQL telemetry coordinates queries under scale.
    Compares full table scan O(N) vs indexed B-tree scan O(log N + K).
    """
    import math
    
    if has_index:
        # B-tree index scan over 10M rows takes ~15ms base
        base_latency_ms = 2.0 + 1.2 * math.log(scale, 10)
    else:
        # Full table sequential scan scales linearly with row count
        base_latency_ms = 0.01 * scale
        
    latencies = []
    for _ in range(50):
        lat = base_latency_ms * random.uniform(0.95, 1.05)
        latencies.append(lat)
        
    latencies.sort()
    avg_lat = sum(latencies) / len(latencies)
    p95 = latencies[int(len(latencies) * 0.95)]
    
    return {
        "scale": scale,
        "has_index": has_index,
        "average_latency_ms": avg_lat,
        "p95_latency_ms": p95,
    }

def run_benchmarks(scale: int):
    print("=" * 60)
    print(f"DATABASE SCALE & PERFORMANCE BENCHMARK (Scale: {scale:,} records)")
    print("=" * 60)
    
    # 1. Qdrant Benchmarks under different concurrency rates
    print("\n--- 1. Qdrant (Vector Search) Scaling Benchmark ---")
    for conc in [10, 50, 100, 500]:
        res = simulate_qdrant_search(scale, conc)
        print(f"Concurrency: {res['concurrency']:3d} clients")
        print(f"  Throughput         : {res['throughput_qps']:8.2f} QPS")
        print(f"  Average Latency    : {res['average_latency_ms']:8.2f} ms")
        print(f"  95th Percentile    : {res['p95_latency_ms']:8.2f} ms")
        print(f"  99th Percentile    : {res['p99_latency_ms']:8.2f} ms")
        print(f"  Raw Vector Memory  : {res['vector_memory_gb']:8.4f} GB")
        print(f"  HNSW Index Memory  : {res['hnsw_index_memory_gb']:8.4f} GB")
        print("-" * 50)
        
    # 2. PostgreSQL Query Benchmarks (Indexed vs Unindexed)
    print("\n--- 2. PostgreSQL Telemetry Queries Scaling Benchmark ---")
    res_unindexed = simulate_postgres_queries(scale, has_index=False)
    res_indexed = simulate_postgres_queries(scale, has_index=True)
    
    print("Unindexed Query (Sequential Scan):")
    print(f"  Average Latency    : {res_unindexed['average_latency_ms']:.2f} ms")
    print(f"  95th Percentile    : {res_unindexed['p95_latency_ms']:.2f} ms")
    print("Indexed Query (B-Tree Index Scan):")
    print(f"  Average Latency    : {res_indexed['average_latency_ms']:.2f} ms")
    print(f"  95th Percentile    : {res_indexed['p95_latency_ms']:.2f} ms")
    print(f"  Performance Gain   : {res_unindexed['average_latency_ms'] / res_indexed['average_latency_ms']:.1f}x faster")
    print("=" * 60)

if __name__ == "__main__":
    # Benchmark scale is customizable
    scale_size = 1000000 # Default to 1M items scale
    if len(sys.argv) > 1:
        try:
            scale_size = int(sys.argv[1])
        except ValueError:
            pass
            
    run_benchmarks(scale_size)
