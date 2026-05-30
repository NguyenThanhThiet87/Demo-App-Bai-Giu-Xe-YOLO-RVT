from .predict_onnx import ONNXEngineWrapper
from .utils import preprocess_image_gpu, parse_yolo_raw_output, index_to_char
import cv2
import numpy as np
import os
import sys

from .predict_tensorRT import TRTEngineWrapper

def load_model(model_path):
    if model_path.endswith('.onnx'):
        return ONNXEngineWrapper(model_path)
    elif model_path.endswith('.engine'):
        return TRTEngineWrapper(model_path)
    raise RuntimeError(f"Chỉ hỗ trợ mô hình .onnx hoặc .engine (Đã nhận được: {model_path})")

def predict_license_plate(model, frame, size=(640, 640)):
    # 1. Preprocess
    image_tensor = preprocess_image_gpu(frame, size)

    # 2. Inference
    outputs_logits, detections = model(image_tensor)
    
    # 3. Postprocess OCR
    # NumPy Softmax
    exp_logits = np.exp(outputs_logits - np.max(outputs_logits, axis=-1, keepdims=True))
    probabilities = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)
    
    max_probs = np.max(probabilities, axis=-1)
    predicted_indices = np.argmax(probabilities, axis=-1)
    
    pred_indices = predicted_indices[0]
    confidences = max_probs[0]
    
    # Tìm EOS token (37) hoặc pad token (38)
    eos_mask = (pred_indices == 37) | (pred_indices == 38)
    if np.any(eos_mask):
        eos_pos = np.nonzero(eos_mask)[0][0]
        pred_indices = pred_indices[:eos_pos]
        confidences = confidences[:eos_pos]
        
    overall_conf = np.mean(confidences).item() if len(confidences) > 0 else 0.0
    predicted_text = index_to_char(pred_indices.tolist(), include_special_tokens=False)

    bbox, conf_det = parse_yolo_raw_output(detections, conf_threshold=0.3, img_size=size)
 
    return predicted_text, overall_conf, (bbox, conf_det)
