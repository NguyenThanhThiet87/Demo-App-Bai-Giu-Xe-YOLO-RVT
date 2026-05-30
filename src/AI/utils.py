import numpy as np
import cv2

#--- Constants ---
MAX_SEQ_LENGTH = 10
CHARACTERS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SOS_TOKEN = 36
EOS_TOKEN = 37
PAD_TOKEN = len(CHARACTERS) + 2
NUM_CLASSES = len(CHARACTERS) + 3  # SOS, EOS, PAD

#--- Utility functions ---
def index_to_char(indices, include_special_tokens=False):
    result = []
    for i in indices:
        if i == SOS_TOKEN:
            if include_special_tokens: result.append('[SOS]')
        elif i == EOS_TOKEN:
            if include_special_tokens: result.append('[EOS]')
            break
        elif 0 <= i < len(CHARACTERS):
            result.append(CHARACTERS[i])
        else:
            if include_special_tokens or i not in [SOS_TOKEN, EOS_TOKEN]:
                result.append(f'[UNK_{i}]')
    return ''.join(result)

def char_to_indices(text):
    indices = [SOS_TOKEN]
    for c in text:
        if c in CHARACTERS:
            indices.append(CHARACTERS.index(c))
        else:
            indices.append(0)
    indices.append(EOS_TOKEN)
    return np.array(indices, dtype=np.int64)

def preprocess_image_gpu(frame, frame_size=(640, 640)):
    # frame: Numpy (H, W, 3) BGR
    # Resize bằng OpenCV
    if frame.shape[:2] != frame_size:
        frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_LINEAR)
    
    # BGR -> RGB
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Chuyển sang float32 và chia 255
    tensor = frame.astype(np.float32) / 255.0
    
    # Chuẩn hóa (Normalize)
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    tensor = (tensor - mean) / std
    
    # HWC -> CHW
    tensor = np.transpose(tensor, (2, 0, 1))
    
    # Thêm batch dimension (1, C, H, W)
    tensor = np.expand_dims(tensor, axis=0)
    
    return tensor

def parse_yolo_raw_output(pred_tensor, conf_threshold=0.3, img_size=(640, 640)):
    # Bóc tách list/tuple nếu có
    if isinstance(pred_tensor, (list, tuple)):
        pred_tensor = pred_tensor[0]
        
    # Xử lý shape: (1, 5, 8400) → (8400, 5)
    if pred_tensor.ndim == 3:
        if pred_tensor.shape[1] == 5:
            # (1, 5, N) → (N, 5)
            pred_tensor = pred_tensor[0].T  
        else:
            # (1, N, 5) → (N, 5)
            pred_tensor = pred_tensor[0]
    elif pred_tensor.ndim == 2 and pred_tensor.shape[0] == 5:
        pred_tensor = pred_tensor.T
        
    # Format: [x_center_PIXEL, y_center_PIXEL, w_PIXEL, h_PIXEL, conf]
    confs = pred_tensor[:, 4]
    mask = confs > conf_threshold
    
    if not np.any(mask):
        return None, 0.0
    
    # Lấy detection có confidence cao nhất
    filtered = pred_tensor[mask]
    best_idx = np.argmax(filtered[:, 4])
    best_det = filtered[best_idx]
    
    # Parse bbox: (x_center, y_center, w, h)
    x_center, y_center, w, h, conf = best_det[:5]
    
    x = int(x_center - w/2)
    y = int(y_center - h/2)
    
    x = max(0, min(x, img_size[0]))
    y = max(0, min(y, img_size[1]))
    w = max(0, min(int(w), img_size[0] - x))
    h = max(0, min(int(h), img_size[1] - y))
    
    bbox = (x, y, w, h)
    
    return bbox, float(conf)