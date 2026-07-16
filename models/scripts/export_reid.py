import argparse
import logging
import os
import sys
import torch

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("models.export_reid")

def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for exporting the ReID model."""
    parser = argparse.ArgumentParser(
        description="Export a pre-trained OSNet ReID model to ONNX format."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="models/reid/osnet_x025_reid.onnx",
        help="Path where the exported ONNX model will be saved."
    )
    return parser.parse_args()

def export_reid_to_onnx(output_path: str) -> str:
    """Downloads the pre-trained OSNet-x0.25 model and exports it to ONNX format.
    
    Args:
        output_path: Target filepath for the exported ONNX file.
        
    Returns:
        The path of the exported ONNX file.
    """
    # 1. Attempt to import torchreid, install if missing
    try:
        import torchreid
    except ImportError:
        logger.warning("torchreid package not found. Attempting to install 'torchreid' automatically...")
        import subprocess
        try:
            # Install direct from git to avoid dependency issues with outdated setup.py on PyPI
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "git+https://github.com/KaiyangZhou/deep-person-reid.git"
            ])
            import torchreid
        except Exception as e:
            logger.error("Failed to install torchreid. Please run: pip install git+https://github.com/KaiyangZhou/deep-person-reid.git")
            raise e

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 2. Build OSNet-x0.25 model structure with pre-trained weights
    logger.info("Initializing OSNet-x0.25 architecture and downloading pre-trained ImageNet weights...")
    model = torchreid.models.build_model(
        name="osnet_x0_25",
        num_classes=1000,
        pretrained=True
    )
    
    # Put model into evaluation mode for static graphs
    model.eval()

    # 3. Create dummy input matching OSNet expected input size [Batch, Channels, Height, Width]
    # OSNet standard inputs are 256x128 images
    logger.info("Generating dummy input of shape [1, 3, 256, 128] for trace...")
    dummy_input = torch.randn(1, 3, 256, 128, dtype=torch.float32)

    # 4. Perform ONNX export
    logger.info(f"Exporting OSNet model to ONNX: {output_path}...")
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=12,          # Standard opset version for DeepStream compatibility
        do_constant_folding=True,  # Optimizes constants during export
        input_names=["input"],
        output_names=["features"], # Match the name in configs/sgie_reid.txt
        dynamic_axes={
            "input": {0: "batch_size"},
            "features": {0: "batch_size"}
        }
    )

    if not os.path.exists(output_path):
        raise RuntimeError("ONNX file was not created successfully.")

    logger.info(f"OSNet ReID model exported successfully to: {output_path}")
    return output_path

def main() -> None:
    """Main execution block."""
    args = parse_arguments()
    try:
        exported_file = export_reid_to_onnx(args.output_path)
        logger.info(f"ONNX Model export complete: {exported_file}")
    except Exception as e:
        logger.error(f"Failed to export ReID model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
