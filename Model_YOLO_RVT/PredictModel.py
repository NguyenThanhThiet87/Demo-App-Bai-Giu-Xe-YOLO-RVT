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
    
    # 2. Đổi trục HWC -> CHW và thêm batch dimension
    tensor = tensor.permute(2, 0, 1).unsqueeze(0) # (1, 3, H, W)
    
    # 3. Chuyển sang FP16 và chia 255
    # Lưu ý: Phải chuyển sang float/half trước khi resize để nội suy chính xác
    tensor = tensor.half() / 255.0 
    
    # 4. RESIZE TRÊN GPU (Thay thế cv2.resize)
    # PyTorch interpolate cực nhanh trên GPU
    if tensor.shape[-2:] != frame_size:
        tensor = F.interpolate(tensor, size=frame_size, mode='bilinear', align_corners=False)
    
    # 5. Normalize (Dùng tensor Mean/Std đã convert sang half ở hàm init)
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

def predict_license_plate(model, frame, size=(640, 640), constrained_length=None):
    # --- Giai đoạn 1: Preprocess ---
    # Không đo thời gian print ở đây nữa để tránh delay I/O
    image_tensor = preprocess_image_gpu(frame, size)

    # --- Giai đoạn 2: Inference ---
    with torch.no_grad():
        outputs_logits = model(image_tensor, target=None, teach_ratio=0.0, forced_output_length=constrained_length)
    
    # --- Giai đoạn 3: Postprocess ---
    # Xử lý ngay trên GPU để giảm tải CPU
    probabilities = torch.softmax(outputs_logits, dim=-1)
    max_probs, predicted_indices = torch.max(probabilities, dim=-1)
    
    # Lấy dữ liệu batch đầu tiên
    pred_indices = predicted_indices[0]
    confidences = max_probs[0]
    
    # Tìm EOS token trên GPU
    eos_mask = (pred_indices == 36) # Giả sử 36 là EOS
    if eos_mask.any():
        eos_pos = torch.nonzero(eos_mask, as_tuple=False)[0, 0].item()
        pred_indices = pred_indices[:eos_pos]
        confidences = confidences[:eos_pos]
        
    # Chỉ copy kết quả cuối cùng về CPU (Nhẹ hơn nhiều so với copy cả mảng to)
    predicted_text = index_to_char(pred_indices.cpu().tolist(), include_special_tokens=False)
    
    confs = confidences.cpu().tolist()
    overall_conf = sum(confs) / len(confs) if confs else 0.0

    return predicted_text, overall_conf
