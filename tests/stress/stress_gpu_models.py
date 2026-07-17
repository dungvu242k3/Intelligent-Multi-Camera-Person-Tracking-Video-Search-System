import time
import argparse
import random

try:
    import torch
    import torch.nn as nn
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    class nn:
        class Module:
            pass

class MockYOLOv8PGIE(nn.Module):
    """Simulates YOLOv8 Object Detection model backbone inference structure."""
    def __init__(self):
        super().__init__()
        # Simulates typical high-level YOLOv8 backbone convolutions
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(16)
        self.relu1 = nn.ReLU(inplace=True)
        
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(32)
        self.relu2 = nn.ReLU(inplace=True)
        
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(64)
        self.relu3 = nn.ReLU(inplace=True)
        
        # Adaptive pooling to output detection grids
        self.pool = nn.AdaptiveAvgPool2d((20, 20))
        self.out_layer = nn.Conv2d(64, 84, kernel_size=1) # 84 classes/boxes format

    def forward(self, x):
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.relu3(self.bn3(self.conv3(x)))
        x = self.pool(x)
        return self.out_layer(x)

class MockOSNetSGIE(nn.Module):
    """Simulates OSNet ReID embedding extraction model backbone inference."""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu1 = nn.ReLU(inplace=True)
        
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.relu2 = nn.ReLU(inplace=True)
        
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(64, 512) # ReID Embedding dimension 512

    def forward(self, x):
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.pool(x)
        x = torch.flatten(x, 1)
        embedding = self.fc(x)
        # Normalize embedding to unit sphere
        return nn.functional.normalize(embedding, p=2, dim=1)

def run_gpu_benchmark(batch_size: int, iterations: int):
    if not _TORCH_AVAILABLE:
        print("=" * 60)
        print("DEEP LEARNING MODEL STRESS BENCHMARK (SIMULATION)".center(60))
        print("=" * 60)
        print("Device Selected       : CPU (Simulated)")
        print(f"Batch Size            : {batch_size}")
        print("Warmup Iterations     : 10")
        print(f"Benchmark Iterations  : {iterations}")
        print("-" * 60)
        
        # YOLOv8: ~150ms per batch
        yolo_avg = 150.0 * (batch_size / 4.0) * random.uniform(0.95, 1.05)
        yolo_p95 = yolo_avg * 1.15
        yolo_fps = (batch_size * iterations) / ((yolo_avg * iterations) / 1000.0)
        
        # OSNet: ~30ms per batch
        osnet_avg = 30.0 * (batch_size / 4.0) * random.uniform(0.95, 1.05)
        osnet_p95 = osnet_avg * 1.15
        osnet_fps = (batch_size * iterations) / ((osnet_avg * iterations) / 1000.0)
        
        print("\nBENCHMARK RESULTS:")
        print("-" * 60)
        print("1. YOLOv8 PGIE Detection Model:")
        print(f"  Average Latency    : {yolo_avg:.2f} ms per batch")
        print(f"  95th Percentile    : {yolo_p95:.2f} ms")
        print(f"  Throughput         : {yolo_fps:.2f} frames/sec (FPS)")
        print("-" * 60)
        print("2. OSNet SGIE ReID Feature Extractor:")
        print(f"  Average Latency    : {osnet_avg:.2f} ms per batch")
        print(f"  95th Percentile    : {osnet_p95:.2f} ms")
        print(f"  Throughput         : {osnet_fps:.2f} crops/sec (CPS)")
        print("-" * 60)
        print("Hardware Platform       : System CPU Multicore (Simulated)")
        print("=" * 60)
        return

    # Determine device
    cuda_available = torch.cuda.is_available()
    device = torch.device("cuda" if cuda_available else "cpu")
    
    print("=" * 60)
    print("DEEP LEARNING MODEL GPU/CPU STRESS BENCHMARK".center(60))
    print("=" * 60)
    print(f"Device Selected       : {device.type.upper()}")
    if cuda_available:
        print(f"GPU Name              : {torch.cuda.get_device_name(0)}")
        print(f"VRAM Capacity         : {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        print("[WARNING] CUDA GPU not found. Falling back to CPU mode benchmark.")
    print(f"Batch Size            : {batch_size}")
    print("Warmup Iterations     : 10")
    print(f"Benchmark Iterations  : {iterations}")
    print("-" * 60)

    # Instantiate models
    yolo = MockYOLOv8PGIE().to(device)
    osnet = MockOSNetSGIE().to(device)
    yolo.eval()
    osnet.eval()

    # Generate dummy input tensors
    # YOLOv8 input is 640x640 frame images
    yolo_input = torch.randn(batch_size, 3, 640, 640, device=device)
    # OSNet crop input is 256x128 crop images
    osnet_input = torch.randn(batch_size, 3, 256, 128, device=device)

    # Warmup
    print("Warming up layers...")
    with torch.no_grad():
        for _ in range(10):
            _ = yolo(yolo_input)
            _ = osnet(osnet_input)
    if cuda_available:
        torch.cuda.synchronize()

    print("Running benchmarking iterations...")
    
    # Benchmark YOLOv8 (PGIE)
    yolo_times = []
    with torch.no_grad():
        for _ in range(iterations):
            start = time.perf_counter()
            _ = yolo(yolo_input)
            if cuda_available:
                torch.cuda.synchronize()
            elapsed = (time.perf_counter() - start) * 1000.0 # ms
            yolo_times.append(elapsed)
            
    # Benchmark OSNet ReID (SGIE)
    osnet_times = []
    with torch.no_grad():
        for _ in range(iterations):
            start = time.perf_counter()
            _ = osnet(osnet_input)
            if cuda_available:
                torch.cuda.synchronize()
            elapsed = (time.perf_counter() - start) * 1000.0 # ms
            osnet_times.append(elapsed)

    # Performance calculations
    yolo_times.sort()
    yolo_avg = sum(yolo_times) / len(yolo_times)
    yolo_p95 = yolo_times[int(len(yolo_times) * 0.95)]
    yolo_fps = (batch_size * iterations) / (sum(yolo_times) / 1000.0)

    osnet_times.sort()
    osnet_avg = sum(osnet_times) / len(osnet_times)
    osnet_p95 = osnet_times[int(len(osnet_times) * 0.95)]
    osnet_fps = (batch_size * iterations) / (sum(osnet_times) / 1000.0)

    print("\nBENCHMARK RESULTS:")
    print("-" * 60)
    print("1. YOLOv8 PGIE Detection Model:")
    print(f"  Average Latency    : {yolo_avg:.2f} ms per batch")
    print(f"  95th Percentile    : {yolo_p95:.2f} ms")
    print(f"  Throughput         : {yolo_fps:.2f} frames/sec (FPS)")
    print("-" * 60)
    print("2. OSNet SGIE ReID Feature Extractor:")
    print(f"  Average Latency    : {osnet_avg:.2f} ms per batch")
    print(f"  95th Percentile    : {osnet_p95:.2f} ms")
    print(f"  Throughput         : {osnet_fps:.2f} crops/sec (CPS)")
    print("-" * 60)
    
    if cuda_available:
        vram_allocated = torch.cuda.memory_allocated(0) / 1024**2 # MB
        vram_max = torch.cuda.max_memory_allocated(0) / 1024**2 # MB
        print(f"Hardware VRAM Allocated : {vram_allocated:.2f} MB")
        print(f"Hardware VRAM Peak Max  : {vram_max:.2f} MB")
    else:
        print("Hardware Platform       : System CPU Multicore")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Pipeline Deep Learning Inference Stress Benchmark")
    parser.add_argument("--batch-size", type=int, default=4, help="Inference batch size (default: 4)")
    parser.add_argument("--iterations", type=int, default=50, help="Number of benchmark loops (default: 50)")
    
    args = parser.parse_args()
    run_gpu_benchmark(args.batch_size, args.iterations)
