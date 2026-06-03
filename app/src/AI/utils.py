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

try:
    import cupy as cp
    cp.cuda.runtime.getDeviceCount()
    USE_GPU = True
    xp = cp
except Exception:
    USE_GPU = False
    xp = np

_mean_tensor = None
_std_tensor = None

def preprocess_image_gpu(frame, frame_size=(640, 640)):
    global _mean_tensor, _std_tensor
    
    # 1. Resize bằng OpenCV (chạy trên CPU vì nhẹ và tối ưu)
    if frame.shape[:2] != frame_size:
        frame = cv2.resize(frame, frame_size, interpolation=cv2.INTER_LINEAR)
    
    # 2. Tải lên mảng bằng uint8 để giảm 4 lần băng thông PCIe, sau đó ép kiểu sang float32 trên GPU
    tensor = xp.asarray(frame)
    tensor = tensor.astype(xp.float32)
    
    # 3. BGR -> RGB swap siêu nhanh bằng zero-copy view trên GPU
    tensor = tensor[..., ::-1]
    
    # 4. Gộp phép chia 255 vào chuẩn hóa để bớt 1 lần tính toán trên toàn ma trận
    if _mean_tensor is None:
        _mean_tensor = xp.array([0.485 * 255.0, 0.456 * 255.0, 0.406 * 255.0], dtype=xp.float32)
        _std_tensor = xp.array([0.229 * 255.0, 0.224 * 255.0, 0.225 * 255.0], dtype=xp.float32)
        
    tensor = (tensor - _mean_tensor) / _std_tensor
    
    # 5. HWC -> CHW và thêm Batch
    tensor = xp.transpose(tensor, (2, 0, 1))
    tensor = xp.expand_dims(tensor, axis=0)
    
    return tensor

def parse_yolo_raw_output(pred_tensor, conf_threshold=0.3, img_size=(640, 640)):
    # pred_tensor có thể là list hoặc tuple, bóc tách nếu có
    if isinstance(pred_tensor, (list, tuple)):
        pred_tensor = pred_tensor[0]
        
    # Hỗ trợ cả numpy và cupy để tăng tốc (không tự động đẩy lên GPU nếu đã là numpy)
    xp_local = np if isinstance(pred_tensor, np.ndarray) else xp
        
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
    
    if not xp_local.any(mask):
        return None, 0.0
    
    # Lấy detection có confidence cao nhất
    filtered = pred_tensor[mask]
    best_idx = xp_local.argmax(filtered[:, 4])
    best_det = filtered[best_idx]
    
    # Lấy giá trị về CPU (chỉ khi có hàm .get của CuPy)
    best_det_cpu = best_det.get() if hasattr(best_det, 'get') else best_det
    
    # Parse bbox: (x_center, y_center, w, h)
    x_center, y_center, w, h, conf = best_det_cpu[:5]
    
    x = int(x_center - w/2)
    y = int(y_center - h/2)
    
    x = max(0, min(x, img_size[0]))
    y = max(0, min(y, img_size[1]))
    w = max(0, min(int(w), img_size[0] - x))
    h = max(0, min(int(h), img_size[1] - y))
    
    bbox = (x, y, w, h)
    
    return bbox, float(conf)