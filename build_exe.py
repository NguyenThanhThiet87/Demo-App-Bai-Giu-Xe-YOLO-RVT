import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Luon dung Python cua .venv de dam bao gom du thu vien AI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, '.venv', 'Scripts', 'python.exe')
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = sys.executable  # fallback

NVIDIA_PKG_DIR = os.path.join(BASE_DIR, '.venv', 'Lib', 'site-packages', 'nvidia')


def cleanup_dist_post_build():
    """Don dep cac file rác va di chuyen CUDA DLL ra thu muc goc de chong trung lap."""
    internal_dir = os.path.join(BASE_DIR, 'dist', 'AI_Parking', '_internal')
    if not os.path.exists(internal_dir):
        return

    print("\n[*] Dang don dep cac file rac va DLL trung lap de toi uu dung luong...")
    saved_bytes = 0

    # 1. Xoa cac file TensorRT phien ban 11 (Vi Python tensorrt dang cai la ban 10)
    # Trong thu muc tensorrt_libs hien tai dang bi duplicate ca 2 bo TRT 10 va TRT 11 (ton 2.2 GB).
    # Vi tensorrt.pyd la ban 10 nen no chi load cac file _10.dll, ta co the xoa toan bo cac file _11.dll ma khong so bi crash.
    trt_libs_dir = os.path.join(internal_dir, 'tensorrt_libs')
    if os.path.exists(trt_libs_dir):
        for f in os.listdir(trt_libs_dir):
            if f.endswith('_11.dll'):
                filepath = os.path.join(trt_libs_dir, f)
                try:
                    size = os.path.getsize(filepath)
                    os.remove(filepath)
                    saved_bytes += size
                    print(f"  [-] Da xoa file TensorRT phien ban cu/thua: {f} (-{size/1024/1024:.1f} MB)")
                except Exception as e:
                    pass

    # 2. Di chuyen TAT CA cac file DLL tu thu muc nvidia ra thu muc goc _internal
    # Vi mot so DLL (nhu nvrtc-builtins) duoc load dong, nen no phai nam cung cho voi nvrtc chinh.
    nvidia_dir = os.path.join(internal_dir, 'nvidia')
    if os.path.exists(nvidia_dir):
        copied = 0
        for root, dirs, files in os.walk(nvidia_dir):
            for file in files:
                if file.endswith('.dll'):
                    src = os.path.join(root, file)
                    dst = os.path.join(internal_dir, file)
                    if not os.path.exists(dst):
                        import shutil
                        shutil.copy2(src, dst)
                        copied += 1
        print(f"  [+] Da di chuyen {copied} file CUDA DLL an ra thu muc goc de dam bao hoat dong on dinh.")
        
        # 3. Xoa toan bo thu muc nvidia de triet tieu su nhan ban (Tiet kiem ~2GB)
        try:
            import shutil
            # Tinh toan dung luong thu muc
            def get_dir_size(path):
                total = 0
                for r, d, f in os.walk(path):
                    for file in f:
                        total += os.path.getsize(os.path.join(r, file))
                return total
            dir_size = get_dir_size(nvidia_dir)
            shutil.rmtree(nvidia_dir)
            saved_bytes += dir_size
            print(f"  [-] Da xoa thu muc nvidia nhan ban (-{dir_size/1024/1024:.1f} MB)")
        except Exception as e:
            print(f"  [-] Khong the xoa thu muc nvidia: {e}")
                            
    print(f"[+] Don dep hoan tat! Tong dung luong tiet kiem duoc: {saved_bytes/1024/1024/1024:.2f} GB")


def get_nvidia_add_data_args():
    """Thu thap cac thu vien CUDA DLL tu nvidia pip packages de nhung vao exe."""
    args = []
    if not os.path.exists(NVIDIA_PKG_DIR):
        print("[!] Khong tim thay thu muc nvidia trong .venv, bo qua CUDA DLLs")
        return args

    for pkg in os.listdir(NVIDIA_PKG_DIR):
        bin_dir = os.path.join(NVIDIA_PKG_DIR, pkg, 'bin')
        if os.path.isdir(bin_dir) and any(f.endswith('.dll') for f in os.listdir(bin_dir)):
            # Source;Dest - copy DLL vao thu muc _internal/nvidia/<pkg>/bin/
            args += ["--add-binary", f"{bin_dir};nvidia/{pkg}/bin"]
            print(f"  [+] Se gom CUDA DLL: nvidia/{pkg}/bin")
    return args


def build_executable():
    print("=" * 60)
    print("[*] BAT DAU QUA TRINH DONG GOI PHAN MEM THANH FILE .EXE (TOI UU DUNG LUONG & HIEU SUAT)")
    print(f"[*] Su dung Python: {VENV_PYTHON}")
    print("=" * 60)

    # Kiem tra va cai PyInstaller vao dung .venv
    try:
        result = subprocess.run([VENV_PYTHON, "-c", "import PyInstaller"], capture_output=True)
        if result.returncode != 0:
            raise ImportError
    except (ImportError, FileNotFoundError):
        print("[*] Chua cai dat PyInstaller trong .venv. Dang tu dong cai dat...")
        subprocess.check_call([VENV_PYTHON, "-m", "pip", "install", "pyinstaller"])

    print("\n[*] Dang thu thap CUDA DLL paths...")
    nvidia_args = get_nvidia_add_data_args()

    cmd = [
        VENV_PYTHON, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--console",  # Giữ lại cửa sổ Console (Terminal) để hiển thị log và tiến trình cho người dùng
        "--name", "AI_Parking",
        "--add-data", "src/models/ONNX;src/models/ONNX",
        "--hidden-import", "tensorrt",
        "--collect-all", "cupy",
        "--collect-all", "cupy_backends",
        "--collect-all", "cupyx",
        "--hidden-import", "graphlib",
        "--hidden-import", "cv2",
        "--hidden-import", "pymongo",
        "--hidden-import", "PySide6",
        "main.py"
    ] + nvidia_args

    print("\n[*] Dang chay lenh PyInstaller (Qua trinh nay co the mat 5-10 phut)...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        # Chay tap lenh don dep toi uu dung luong va chong trung lap DLL sau khi build xong
        cleanup_dist_post_build()
        
        # Copy file .env vao thu muc chinh de nguoi dung co the chinh sua thong tin ket noi
        if os.path.exists(".env"):
            import shutil
            dest_env = os.path.join("dist", "AI_Parking", ".env")
            shutil.copy2(".env", dest_env)
            print("[+] Da copy file .env ra thu muc dist/AI_Parking/")

        print("=" * 60)
        print("[+] DONG GOI HOAN TAT!")
        print("[+] Tim thay phan mem tai: dist/AI_Parking/")
        print("[+] Luu y: Hay copy TOAN BO thu muc AI_Parking sang may khac")
        print("=" * 60)
    else:
        print("=" * 60)
        print("[-] DONG GOI THAT BAI! Kiem tra log ben tren de tim loi.")
        print("=" * 60)

if __name__ == "__main__":
    build_executable()
