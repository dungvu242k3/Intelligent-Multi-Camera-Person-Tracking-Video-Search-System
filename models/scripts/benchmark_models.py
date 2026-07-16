import argparse
import logging
import os
import sys
import time
from typing import Tuple, List, Optional
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("models.benchmark")

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for benchmarking."""
    parser = argparse.ArgumentParser(
        description="Benchmark latency and throughput (FPS) for exported ONNX models or TensorRT engines."
    )
    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to the ONNX (.onnx) model or TensorRT (.engine/.trt) file."
    )
    parser.add_argument(
        "--input-shape",
        type=str,
        default="1,3,640,640",
        help="Comma-separated input shape dimensions (e.g. '1,3,640,640' for YOLO, '1,3,256,128' for ReID)."
    )
    parser.add_argument(
        "--num-runs",
        type=int,
        default=100,
        help="Number of inference iterations to run during benchmarking."
    )
    parser.add_argument(
        "--warmup-runs",
        type=int,
        default=10,
        help="Number of initial warmup iterations (excluded from statistics)."
    )
    return parser.parse_args()

def parse_input_shape(shape_str: str) -> Tuple[int, ...]:
    """Converts a comma-separated string to a tuple of integers."""
    try:
        return tuple(int(x.strip()) for x in shape_str.split(","))
    except ValueError as e:
        raise ValueError(f"Invalid input shape format '{shape_str}'. Must be comma-separated integers.") from e

def benchmark_onnx(model_path: str, input_shape: Tuple[int, ...], num_runs: int, warmup_runs: int) -> None:
    """Benchmarks an ONNX model using ONNX Runtime."""
    try:
        import onnxruntime as ort
    except ImportError as e:
        logger.error("onnxruntime is not installed. Run: pip install onnxruntime-gpu (or onnxruntime)")
        raise e

    logger.info(f"Loading ONNX model from: {model_path}")
    
    # Enable GPU provider if available, fallback to CPU
    available_providers = ort.get_available_providers()
    provider = "CUDAExecutionProvider" if "CUDAExecutionProvider" in available_providers else "CPUExecutionProvider"
    logger.info(f"Using execution provider: {provider}")
    
    session = ort.InferenceSession(model_path, providers=[provider])
    input_name = session.get_inputs()[0].name
    
    # Generate dummy input matching shape
    dummy_input = np.random.randn(*input_shape).astype(np.float32)
    
    logger.info(f"Starting {warmup_runs} warmup runs...")
    for _ in range(warmup_runs):
        session.run(None, {input_name: dummy_input})
        
    logger.info(f"Running benchmark with {num_runs} iterations...")
    latencies = []
    
    for _ in range(num_runs):
        start_time = time.perf_counter()
        session.run(None, {input_name: dummy_input})
        end_time = time.perf_counter()
        latencies.append((end_time - start_time) * 1000) # Convert to ms

    print_results(latencies)

def benchmark_tensorrt(model_path: str, input_shape: Tuple[int, ...], num_runs: int, warmup_runs: int) -> None:
    """Benchmarks a TensorRT engine using the tensorrt and pycuda/cupy libraries."""
    try:
        import tensorrt as trt
        import pycuda.driver as cuda
        import pycuda.autoinit  # Required to initialize CUDA context
    except ImportError as e:
        logger.error(
            "TensorRT or PyCUDA Python bindings are missing. "
            "Benchmarking TensorRT engines requires: pip install tensorrt pycuda"
        )
        raise e

    logger.info(f"Loading TensorRT Engine from: {model_path}")
    trt_logger = trt.Logger(trt.Logger.WARNING)
    
    with open(model_path, "rb") as f, trt.Runtime(trt_logger) as runtime:
        engine = runtime.deserialize_cuda_engine(f.read())
        
    if not engine:
        raise RuntimeError("Failed to deserialize TensorRT engine file.")

    with engine.create_execution_context() as context:
        # Determine bindings and allocate device memory
        # In TensorRT 8.5+, context.set_input_shape() is used for dynamic shapes
        # For simplicity, we assume binding index 0 is input
        context.set_input_shape(engine.get_tensor_name(0), input_shape)
        
        # Allocate memory buffers
        h_input = cuda.pagelocked_empty(trt.volume(input_shape), dtype=np.float32)
        h_input[:] = np.random.randn(*input_shape).astype(np.float32).ravel()
        
        # Get output shape
        output_name = engine.get_tensor_name(1)
        output_shape = context.get_tensor_shape(output_name)
        h_output = cuda.pagelocked_empty(trt.volume(output_shape), dtype=np.float32)
        
        # Allocate device memory
        d_input = cuda.mem_alloc(h_input.nbytes)
        d_output = cuda.mem_alloc(h_output.nbytes)
        
        stream = cuda.Stream()
        
        # Bindings mappings
        bindings = [int(d_input), int(d_output)]
        
        logger.info(f"Starting {warmup_runs} warmup runs...")
        for _ in range(warmup_runs):
            cuda.memcpy_htod_async(d_input, h_input, stream)
            context.execute_async_v3(stream_handle=stream.handle)
            cuda.memcpy_dtoh_async(h_output, d_output, stream)
            stream.synchronize()
            
        logger.info(f"Running benchmark with {num_runs} iterations...")
        latencies = []
        
        for _ in range(num_runs):
            start_time = time.perf_counter()
            cuda.memcpy_htod_async(d_input, h_input, stream)
            context.execute_async_v3(stream_handle=stream.handle)
            cuda.memcpy_dtoh_async(h_output, d_output, stream)
            stream.synchronize()
            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000) # Convert to ms
            
        print_results(latencies)

def print_results(latencies: List[float]) -> None:
    """Computes and prints benchmarking statistics."""
    latencies_np = np.array(latencies)
    avg_latency = np.mean(latencies_np)
    median_latency = np.median(latencies_np)
    min_latency = np.min(latencies_np)
    max_latency = np.max(latencies_np)
    p95_latency = np.percentile(latencies_np, 95)
    fps = 1000.0 / avg_latency
    
    logger.info("================ Benchmark Results ================")
    logger.info(f"Iterations:      {len(latencies)}")
    logger.info(f"Average Latency: {avg_latency:.3f} ms")
    logger.info(f"Median Latency:  {median_latency:.3f} ms")
    logger.info(f"P95 Latency:     {p95_latency:.3f} ms")
    logger.info(f"Range:           {min_latency:.3f} ms - {max_latency:.3f} ms")
    logger.info(f"Throughput:      {fps:.2f} FPS")
    logger.info("===================================================")

def main() -> None:
    """Main execution block."""
    args = parse_arguments()
    
    try:
        input_shape = parse_input_shape(args.input_shape)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
        
    model_ext = os.path.splitext(args.model_path)[1].lower()
    
    try:
        if model_ext == ".onnx":
            benchmark_onnx(args.model_path, input_shape, args.num_runs, args.warmup_runs)
        elif model_ext in [".engine", ".trt"]:
            benchmark_tensorrt(args.model_path, input_shape, args.num_runs, args.warmup_runs)
        else:
            logger.error(f"Unsupported model file format: '{model_ext}'. Supported formats: .onnx, .engine, .trt")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Benchmarking session failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
