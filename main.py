
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
  
import sys
from PySide6.QtWidgets import QApplication
# Nạp app_controller (chứa onnxruntime) TRƯỚC để thiết lập đúng các thư mục DLL CUDA 12
from src.scores.app_controller import System
import subprocess

BEST_CONFIDENCE_THRESHOLD = 0.8
MAX_FRAME_HISTORY = 1000
MAX_FRAME_STOPPING = 15
IMG_SIZE_MODEL = (640, 640)
FRAME_SIZE = (1280, 1080)
FPS_CAMERA = 60

def get_gpu_name():
    try:
        import subprocess
        import re
        # Lấy tên GPU hiện tại (VD: NVIDIA GeForce RTX 3050 Ti)
        gpu_name = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
            encoding='utf-8'
        ).strip().split('\n')[0]
        # Chuyển thành dạng snake_case (nvidia_geforce_rtx_3050_ti)
        gpu_name_clean = re.sub(r'[^a-zA-Z0-9]+', '_', gpu_name).strip('_').lower()
        return gpu_name_clean
    except Exception:
        return "unknown_gpu"

if __name__ == '__main__':
    from utils_path import resource_path
    
    app = QApplication(sys.argv)
    
    gpu_name = get_gpu_name()
    PATH_MODEL = resource_path(f"src/models/TensorRT/yolo_rvit_v11s_gru_local_{gpu_name}.engine")
    PATH_ONNX = resource_path(r"src/models/ONNX/yolo_rvit_full.onnx")

    if getattr(sys, 'frozen', False):
        # Khi đóng gói exe: chỉ kiểm tra file engine có tồn tại không
        import os
        if not os.path.exists(PATH_MODEL):
            print("[*] Không tìm thấy file engine TensorRT. Chuyển sang chạy file ONNX...")
            PATH_MODEL = PATH_ONNX
        else:
            print(f"[*] Tìm thấy engine TensorRT: {PATH_MODEL}")
    else:
        # Khi chạy từ source: gọi subprocess để kiểm tra/build TensorRT engine
        trt_script = resource_path("trt_builder.py")
        try:
            print("[*] Đang kiểm tra/build TensorRT engine trong tiến trình con...")
            result = subprocess.run(
                [sys.executable, trt_script, PATH_ONNX, PATH_MODEL],
                capture_output=False
            )
            if result.returncode != 0:
                print("[-] Lỗi TensorRT (tiến trình build thất bại). Chuyển sang chạy file ONNX...")
                PATH_MODEL = PATH_ONNX
        except Exception as e:
            print(f"[-] Lỗi subprocess TensorRT: {e}. Chuyển sang chạy file ONNX...")
            PATH_MODEL = PATH_ONNX

    # Khởi chạy hệ thống với cơ chế tự động lùi (fallback) an toàn
    try:
        system = System(PATH_MODEL, gpu_name)
    except Exception as e:
        if PATH_MODEL != PATH_ONNX:
            print(f"[-] Không thể nạp mô hình TensorRT {PATH_MODEL} (Lỗi: {e}). Đang tự động lùi về sử dụng mô hình ONNX...")
            PATH_MODEL = PATH_ONNX
            system = System(PATH_MODEL, gpu_name)
        else:
            raise e
            
    system.start()
    sys.exit(app.exec_())