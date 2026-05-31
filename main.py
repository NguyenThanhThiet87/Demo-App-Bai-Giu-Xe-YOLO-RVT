
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# --- BOOTSTRAP: Thiết lập đường dẫn CUDA DLL khi chạy dưới dạng file .exe đóng gói ---
# Khi PyInstaller đóng gói, các DLL nằm trong thư mục _internal (cùng cấp với .exe)
# CuPy và ONNXRuntime cần biết đường dẫn này để tải đúng cudart64_12.dll, cublas64_12.dll, v.v.
if getattr(sys, 'frozen', False):
    # Thư mục chứa file .exe
    _exe_dir = os.path.dirname(sys.executable)
    # Thư mục _internal chứa tất cả các thư viện được đóng gói
    _internal_dir = os.path.join(_exe_dir, '_internal')
    
    # Thêm _internal vào đầu PATH để Windows tìm DLL ở đây trước
    if _internal_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = _internal_dir + os.pathsep + os.environ.get('PATH', '')
    
    # Cũng thêm vào CUDA_PATH để CuPy tìm thấy
    os.environ.setdefault('CUDA_PATH', _internal_dir)
    
    # Dùng os.add_dll_directory (Python 3.8+) để đăng ký thư mục tìm kiếm DLL
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(_internal_dir)
        # Cũng đăng ký thư mục gốc exe
        os.add_dll_directory(_exe_dir)

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
    import sys
    import os
    import subprocess
    import atexit

    # --- Đóng vai trò là tiến trình con để Build TensorRT nếu được gọi bằng tham số ---
    if len(sys.argv) == 4 and sys.argv[1] == '--build-trt':
        path_onnx = sys.argv[2]
        path_model = sys.argv[3]
        try:
            from TRTUtils import TensorRTConverter
            converter = TensorRTConverter()
            if not converter.check_engine_compatibility(path_model):
                print("[*] Phát hiện engine không tương thích. Đang tiến hành build lại cho GPU này...")
                success = converter.convert_onnx_to_engine(path_onnx, path_model)
                sys.exit(0 if success else 1)
            else:
                sys.exit(0)
        except Exception as e:
            print(f"[-] Lỗi TensorRT subprocess: {e}")
            sys.exit(1)

    # --- Logic chính của chương trình ---
    def reset_gpu_clocks():
        try:
            print("\n[*] Đang khôi phục GPU về chế độ an toàn tự động làm mát...")
            subprocess.run(['nvidia-smi', '-rgc'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except:
            pass

    # Đăng ký chạy hàm reset khi tắt app
    atexit.register(reset_gpu_clocks)

    from utils_path import resource_path
    
    app = QApplication(sys.argv)
    
    gpu_name = get_gpu_name()
    PATH_MODEL = resource_path(f"src/models/TensorRT/yolo_rvit_v11s_gru_local_{gpu_name}.engine")
    PATH_ONNX = resource_path(r"src/models/ONNX/yolo_rvit_full.onnx")

    # Tự động gọi quy trình Build TensorRT (tách process để giải phóng bộ nhớ GPU sau khi build)
    try:
        if getattr(sys, 'frozen', False):
            # Nếu chạy bằng file .exe, gọi lại chính file .exe với tham số ngầm
            trt_cmd = [sys.executable, '--build-trt', PATH_ONNX, PATH_MODEL]
        else:
            # Nếu chạy bằng file python, gọi file trt_builder.py
            trt_script = resource_path("trt_builder.py")
            trt_cmd = [sys.executable, trt_script, PATH_ONNX, PATH_MODEL]

        print("[*] Đang kiểm tra/build TensorRT engine trong tiến trình con...")
        result = subprocess.run(
            trt_cmd,
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