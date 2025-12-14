import torch
import cv2
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils import index_to_char, DEVICE
from YOLO_RViT import YOLO_RViT

# Khởi tạo tensor normalization trên GPU
MEAN_TENSOR = torch.tensor([0.485, 0.456, 0.406], device=DEVICE).view(1, 3, 1, 1)
STD_TENSOR = torch.tensor([0.229, 0.224, 0.225], device=DEVICE).view(1, 3, 1, 1)

import torch.nn.functional as F

def preprocess_image_gpu(frame, frame_size=(640, 640)):
    # 1. Chuyển Numpy (CPU) -> Tensor (GPU) ngay lập tức
    # frame đang là (H, W, 3) uint8 -> copy lên VRAM rất nhẹ
    tensor = torch.from_numpy(frame).to(DEVICE, non_blocking=True)
    
    # 3. Đổi trục HWC -> CHW và thêm batch dimension
    tensor = tensor.permute(2, 0, 1).unsqueeze(0) # (1, 3, H, W)
    
    # 4. Chuyển sang FP16 và chia 255
    # Lưu ý: Phải chuyển sang float/half trước khi resize để nội suy chính xác
    tensor = tensor.half() / 255.0 
    
    # 5. RESIZE TRÊN GPU (Thay thế cv2.resize)
    # PyTorch interpolate cực nhanh trên GPU
    if tensor.shape[-2:] != frame_size:
        tensor = F.interpolate(tensor, size=frame_size, mode='bilinear', align_corners=False)
    
    # 6. Normalize (Dùng tensor Mean/Std đã convert sang half ở hàm init)
    # Đảm bảo MEAN_TENSOR và STD_TENSOR cũng phải là .half()
    tensor = (tensor - MEAN_TENSOR.half()) / STD_TENSOR.half()
    
    return tensor

def load_model_for_prediction(checkpoint_path, yolo_base_model_path, size=(640,640)):
    model = YOLO_RViT(yolo_path=yolo_base_model_path, yolo_target_feature_layer_idx=13)
    # Load vào CPU trước để tránh lỗi memory fragment
    checkpoint = torch.load(checkpoint_path, map_location='cuda', weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    
    model.to(DEVICE)
    model.eval()
    
    # Convert model sang FP16 để chạy nhanh trên 3090/3050Ti
    if DEVICE == 'cuda':
        model.half()

    return model

def parse_yolo_raw_output(raw_output, conf_threshold=0.3, img_size=(640, 640)):
    pred_tensor = raw_output[0]  # (B, 5, N) hoặc (B, N, 5)
    
    # Xử lý shape: (1, 5, 8400) → (8400, 5)
    if pred_tensor.dim() == 3:
        if pred_tensor.shape[1] == 5:
            # (B, 5, N) → (N, 5)
            pred_tensor = pred_tensor[0].T  # (5, N) → (N, 5)
        else:
            # (B, N, 5) → (N, 5)
            pred_tensor = pred_tensor[0]
    
    # Format: [x_center_PIXEL, y_center_PIXEL, w_PIXEL, h_PIXEL, conf]
    # Lọc theo confidence
    confs = pred_tensor[:, 4]
    mask = confs > conf_threshold
    
    if not mask.any():
        return None, 0.0
    
    # Lấy detection có confidence cao nhất
    filtered = pred_tensor[mask]
    best_idx = filtered[:, 4].argmax()
    best_det = filtered[best_idx]
    
    # Parse bbox: (x_center, y_center, w, h) → (x_top_left, y_top_left, w, h)
    x_center, y_center, w, h, conf = best_det[:5].cpu().numpy()
    
    # ✅ GIÁ TRỊ ĐÃ LÀ PIXEL, KHÔNG CẦN NHÂN img_size
    # Chỉ cần convert sang top-left corner
    x = int(x_center - w/2)
    y = int(y_center - h/2)
    
    # Clamp về [0, img_size] để tránh vượt biên
    x = max(0, min(x, img_size[0]))
    y = max(0, min(y, img_size[1]))
    w = max(0, min(int(w), img_size[0] - x))
    h = max(0, min(int(h), img_size[1] - y))
    
    bbox = (x, y, w, h)
    
    return bbox, float(conf)

def predict_license_plate(model, frame, size=(640, 640), constrained_length=None):
    # --- Giai đoạn 1: Preprocess ---
    image_tensor = preprocess_image_gpu(frame, size)

    # --- Giai đoạn 2: Inference ---
    with torch.no_grad():
        outputs_logits, detections = model(image_tensor, target=None, teach_ratio=0.0, forced_output_length=constrained_length)
    
    # --- Giai đoạn 3: Postprocess OCR ---
    probabilities = torch.softmax(outputs_logits, dim=-1)
    max_probs, predicted_indices = torch.max(probabilities, dim=-1)
    
    pred_indices = predicted_indices[0]
    confidences = max_probs[0]
    
    # Tìm EOS token
    eos_mask = (pred_indices == 36)
    if eos_mask.any():
        eos_pos = torch.nonzero(eos_mask, as_tuple=False)[0, 0].item()
        pred_indices = pred_indices[:eos_pos]
        confidences = confidences[:eos_pos]
        
    overall_conf = torch.mean(confidences).item() if len(confidences) > 0 else 0.0
    predicted_text = index_to_char(pred_indices.cpu().tolist(), include_special_tokens=False)

    # --- Giai đoạn 4: Parse bbox ---
    bbox, conf_det = parse_yolo_raw_output(detections, conf_threshold=0.3, img_size=size)

    return predicted_text, overall_conf, (bbox, conf_det)