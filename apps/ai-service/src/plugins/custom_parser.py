"""
Custom YOLO output parser plugin for DeepStream nvinfer.

DeepStream expects a custom bounding box parser function when the model output
is not in the standard YOLO format understood natively by DeepStream.

YOLOv8 uses a different output layout than YOLOv5:
  - Output shape: [batch, 84, 8400] (for 4 classes: [batch, 8, 8400])
  - Where 8 = 4 bbox coords + 4 class scores (no objectness score)

This parser is registered in pgie_yolov8.txt via:
  custom-lib-path=...libcustom_parser.so
  parse-bbox-func-name=NvDsInferParseCustomYolov8

IMPORTANT: For production, compile this into a .so using the DeepStream Python
parser wrapper or use a C++ parser. The Python function below is for reference.
"""

import logging
from typing import List, Tuple

logger = logging.getLogger("ai_service.parser")


def parse_yolov8_output(
    output_layers,
    network_info,
    detection_params,
    layer_names: List[str],
    max_batch_size: int,
) -> List[List[Tuple]]:
    """Parse YOLOv8 model outputs into DeepStream bounding box format.
    
    YOLOv8 output: [batch_size, num_classes + 4, num_anchors]
    where num_anchors = 8400 for 640x640 input.
    
    Returns list of detection lists per batch item.
    Each detection: (x_center, y_center, width, height, class_id, confidence)
    
    NOTE: In production, this runs as a compiled C/C++ shared library
    via the `custom-lib-path` and `parse-bbox-func-name` config params.
    """
    import numpy as np
    
    detections_per_batch = []
    conf_threshold = detection_params.get("pre-threshold", 0.25)
    
    # Find the output layer (usually named "output0" for YOLOv8)
    output_data = None
    for i, name in enumerate(layer_names):
        if name in ("output0", "output", "/model.22/Concat_3_output_0"):
            output_data = output_layers[i]
            break
    
    if output_data is None:
        logger.error("Could not find YOLOv8 output layer — check output-blob-names in config")
        return [[]] * max_batch_size
    
    # output shape: [batch, 8, 8400] for 4 classes
    # Transpose to [batch, 8400, 8] for easier indexing
    out = np.array(output_data)
    if out.ndim == 3:
        out = out.transpose(0, 2, 1)  # [batch, anchors, channels]
    
    for batch_idx in range(min(max_batch_size, out.shape[0])):
        anchors = out[batch_idx]  # [8400, 8]
        
        # Split: first 4 = bbox (cx, cy, w, h), rest = class scores
        bboxes = anchors[:, :4]
        scores = anchors[:, 4:]
        
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)
        
        mask = confidences > conf_threshold
        
        detections = []
        for idx in np.where(mask)[0]:
            cx, cy, w, h = bboxes[idx]
            cls_id = int(class_ids[idx])
            conf = float(confidences[idx])
            detections.append((float(cx), float(cy), float(w), float(h), cls_id, conf))
        
        detections_per_batch.append(detections)
    
    return detections_per_batch
