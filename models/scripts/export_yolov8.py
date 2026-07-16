import argparse
import logging
import os
import sys

# Ensure structured logging is configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("models.export_yolov8")

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for exporting the YOLOv8 model."""
    parser = argparse.ArgumentParser(
        description="Export a pre-trained or custom YOLOv8 model from PyTorch (.pt) to ONNX format."
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="yolov8n",
        help="Name of the pre-trained YOLOv8 model (e.g., yolov8n, yolov8s, yolov8m)."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/yolo",
        help="Target directory where the exported ONNX model will be stored."
    )
    return parser.parse_args()

def export_to_onnx(model_name: str, output_dir: str) -> str:
    """Loads a YOLOv8 model and exports it to ONNX format with dynamic shape support.
    
    Args:
        model_name: The name or path of the PyTorch weights (.pt) file.
        output_dir: The directory to save the exported ONNX model.
        
    Returns:
        The absolute path to the exported ONNX model.
    """
    try:
        from ultralytics import YOLO
    except ImportError as e:
        logger.error(
            "The 'ultralytics' package is not installed. Please install it using: pip install ultralytics"
        )
        raise e

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if we are loading a local .pt file or downloading a pre-trained model
    model_path = model_name if model_name.endswith(".pt") else f"{model_name}.pt"
    logger.info(f"Loading YOLOv8 model weights from: {model_path}")
    model = YOLO(model_path)

    logger.info("Initiating ONNX export with dynamic shape configuration...")
    # opset=12 is recommended for wide compatibility with TensorRT 10.x/8.x in DeepStream
    exported_path = model.export(
        format="onnx",
        dynamic=True,      # Enables dynamic batching and image size
        opset=12,          # Standard opset version for DeepStream integration
        simplify=True      # Simplifies graph nodes for efficient TensorRT compilation
    )

    if not exported_path:
        raise RuntimeError("Export process completed but returned an empty path.")

    # Move the exported ONNX file to the target output directory
    filename = os.path.basename(exported_path)
    target_path = os.path.join(output_dir, filename)
    
    if os.path.abspath(exported_path) != os.path.abspath(target_path):
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(exported_path, target_path)
        logger.info(f"Relocated exported model file to: {target_path}")
    else:
        logger.info(f"ONNX model saved successfully to: {target_path}")

    return target_path

def main() -> None:
    """Main execution block."""
    args = parse_arguments()
    try:
        exported_file = export_to_onnx(args.model_name, args.output_dir)
        logger.info(f"ONNX model export successful: {exported_file}")
    except Exception as e:
        logger.error(f"Failed to export YOLOv8 model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
