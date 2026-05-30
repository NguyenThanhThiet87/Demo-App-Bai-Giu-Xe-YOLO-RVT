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

if __name__ == '__main__':
    from utils_path import resource_path
    
    app = QApplication(sys.argv)
    PATH_MODEL = resource_path(r"AI/TensorRT/yolo_rvit_v11s_gru_local_3050ti.engine")
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

    # Khởi chạy hệ thống với file Model
    system = System(PATH_MODEL)
    system.start()
    sys.exit(app.exec_())