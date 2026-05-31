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


def copy_cuda_dlls_post_build():
    """Sau khi build, copy them cac CUDA DLL can thiet vao thu muc _internal de onnxruntime tim thay."""
    internal_dir = os.path.join(BASE_DIR, 'dist', 'AI_Parking', '_internal')
    if not os.path.exists(NVIDIA_PKG_DIR) or not os.path.exists(internal_dir):
        return

    print("\n[*] Dang copy CUDA DLLs vao thu muc dist...")
    copied = 0
    for pkg in os.listdir(NVIDIA_PKG_DIR):
        bin_dir = os.path.join(NVIDIA_PKG_DIR, pkg, 'bin')
        if os.path.isdir(bin_dir):
            for dll in os.listdir(bin_dir):
                if dll.endswith('.dll'):
                    src = os.path.join(bin_dir, dll)
                    dst = os.path.join(internal_dir, dll)
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        copied += 1
    print(f"[+] Da copy {copied} CUDA DLL files vao _internal/")


def build_executable():
    print("=" * 60)
    print("[*] BAT DAU QUA TRINH DONG GOI PHAN MEM THANH FILE .EXE")
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
        "--windowed",
        "--name", "AI_Parking",
        "--add-data", "src/models/ONNX;src/models/ONNX",
        "--hidden-import", "tensorrt",
        "--hidden-import", "cupy",
        "--hidden-import", "cv2",
        "--hidden-import", "pymongo",
        "--hidden-import", "PySide6",
    ] + nvidia_args + ["main.py"]

    print("\n[*] Dang chay lenh PyInstaller (Qua trinh nay co the mat 5-10 phut)...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        # Copy them CUDA DLL vao thu muc _internal sau khi build xong
        copy_cuda_dlls_post_build()
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
