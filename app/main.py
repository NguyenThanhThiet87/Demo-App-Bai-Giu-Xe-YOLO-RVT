
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
        
    # --- MONKEYPATCH: Sửa lỗi CuPy tìm thư mục bin không tồn tại khi đóng gói ---
    try:
        import cupy._environment
        _orig_setup = cupy._environment._setup_win32_dll_directory
        def safe_setup_win32_dll_directory():
            try:
                _orig_setup()
            except Exception:
                # Bỏ qua lỗi FileNotFoundError khi không tìm thấy thư mục CUDA bin trên máy người dùng
                pass
        cupy._environment._setup_win32_dll_directory = safe_setup_win32_dll_directory
    except Exception:
        pass
# --- IMPORTS ---
import re
import atexit
import subprocess
import runpy
from PySide6.QtWidgets import QApplication

# Nạp app_controller (chứa onnxruntime) TRƯỚC để thiết lập đúng các thư mục DLL CUDA 12
from src.scores.app_controller import System
from utils_path import resource_path
from TRTUtils import TensorRTConverter

BEST_CONFIDENCE_THRESHOLD = 0.8
MAX_FRAME_HISTORY = 1000
MAX_FRAME_STOPPING = 15
IMG_SIZE_MODEL = (640, 640)
FRAME_SIZE = (1280, 1080)
FPS_CAMERA = 60

def get_gpu_name():
    try:
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
    # --- Đóng vai trò là tiến trình con để chạy module python khi gọi từ cupy/cuda.pathfinder (e.g. -m) ---
    if len(sys.argv) > 2 and sys.argv[1] == '-m':
        sys.argv.pop(1)  # Bỏ '-m'
        mod_name = sys.argv[1]
        sys.argv[0] = sys.argv.pop(1)  # Đưa tên module thành script chính
        try:
            runpy.run_module(mod_name, run_name='__main__', alter_sys=True)
        except SystemExit as se:
            sys.exit(se.code)
        except Exception:
            import traceback
            traceback.print_exc()
            sys.exit(1)
        sys.exit(0)

    # --- Đóng vai trò là tiến trình con để Build TensorRT nếu được gọi bằng tham số ---
    if len(sys.argv) == 4 and sys.argv[1] == '--build-trt':
        path_onnx = sys.argv[2]
        path_model = sys.argv[3]
        try:
            converter = TensorRTConverter()
            if converter.check_engine_compatibility(path_model):
                sys.exit(0)
                
            print("[*] Phát hiện engine không tương thích. Đang tiến hành build lại cho GPU này...")
            
            import tkinter as tk
            from tkinter import ttk
            import threading
            
            splash = tk.Tk()
            splash.overrideredirect(True)
            splash.attributes('-topmost', True) # Bắt buộc cửa sổ nổi lên trên cùng
            splash.configure(bg='#1e1e1e', highlightbackground='#00aa00', highlightthickness=2)
            
            width, height = 450, 160
            x = (splash.winfo_screenwidth() // 2) - (width // 2)
            y = (splash.winfo_screenheight() // 2) - (height // 2)
            splash.geometry(f'{width}x{height}+{x}+{y}')
            
            lbl_title = tk.Label(splash, text="TỐI ƯU HÓA MÔ HÌNH AI", font=("Helvetica", 14, "bold"), bg='#1e1e1e', fg='white')
            lbl_title.pack(pady=(25, 10))
            
            lbl_loading = tk.Label(splash, text="Đang biên dịch TensorRT Engine cho GPU của bạn...\nQuá trình này có thể mất từ 1-5 phút (Xin đừng tắt phần mềm).", font=("Helvetica", 10), bg='#1e1e1e', fg='#00ff00')
            lbl_loading.pack(pady=(0, 15))

            progress = ttk.Progressbar(splash, orient="horizontal", length=350, mode="indeterminate")
            progress.pack()
            
            def do_build():
                # Ép giao diện vẽ xong hoàn chỉnh trước khi block luồng chính
                splash.update_idletasks()
                splash.update()
                
                # Chạy build trực tiếp (blocking) trên luồng chính
                success = converter.convert_onnx_to_engine(path_onnx, path_model)
                splash.destroy()
                os._exit(0 if success else 1)
                
            # Đợi 200ms để Linux (X11) kịp vẽ cửa sổ lên màn hình rồi mới chạy build
            splash.after(200, do_build)
            splash.mainloop()
            
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
            # Nếu chạy bằng file python, gọi lại chính file main.py với tham số để kích hoạt giao diện build
            trt_cmd = [sys.executable, __file__, '--build-trt', PATH_ONNX, PATH_MODEL]

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