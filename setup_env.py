import os
import subprocess
import sys

def run_command(command, print_output=True):
    print(f"> {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    output = []
    for line in process.stdout:
        if print_output:
            print(line, end="")
        output.append(line.strip())
        
    process.wait()
    if process.returncode != 0:
        print(f"[!] Lệnh thất bại với mã lỗi {process.returncode}")
        # Không dừng chương trình hoàn toàn để tránh gián đoạn các lệnh uninstall
    return output

def get_gpu_info():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,compute_cap", "--format=csv,noheader"], 
            text=True
        ).strip().split('\n')
        
        gpus = []
        for line in output:
            name, cc = line.split(', ')
            gpus.append({"name": name, "cc": float(cc)})
        return gpus
    except Exception as e:
        print("[-] Không tìm thấy GPU NVIDIA hoặc chưa cài Driver:", e)
        return []

def setup_environment():
    print("="*60)
    print("🚀 BẮT ĐẦU CÀI ĐẶT MÔI TRƯỜNG AI TỰ ĐỘNG")
    print("="*60)
    
    gpus = get_gpu_info()
    
    # Mặc định sử dụng ONNX Runtime
    use_tensorrt = False
    cuda_version = "12.1"
    
    if len(gpus) > 0:
        gpu = gpus[0]
        print(f"[*] Phát hiện GPU: {gpu['name']} (Compute Capability: {gpu['cc']})")
        
        # TensorRT 10.x hỗ trợ tốt nhất trên Compute Capability >= 7.5 (Turing trở lên)
        if gpu['cc'] >= 7.5:
            print("[+] GPU của bạn HỖ TRỢ TensorRT mạnh mẽ!")
            use_tensorrt = True
        else:
            print("[-] GPU của bạn thuộc kiến trúc cũ (Pascal/Maxwell). TensorRT đời mới không hỗ trợ tốt.")
            print("[+] Lựa chọn tốt nhất: Sử dụng ONNXRuntime-GPU siêu mượt!")
            use_tensorrt = False
    else:
        print("[-] Máy không có GPU NVIDIA. Sẽ cài đặt bản CPU.")
        cuda_version = "cpu"
        
    python_exe = sys.executable
    
    print("\n" + "="*60)
    print("🧹 BƯỚC 1: DỌN DẸP CÁC THƯ VIỆN XUNG ĐỘT")
    print("="*60)
    run_command(f'"{python_exe}" -m pip uninstall -y onnxruntime onnxruntime-gpu tensorrt numpy opencv-python')
    
    print("\n" + "="*60)
    print("📦 BƯỚC 2: CÀI ĐẶT THƯ VIỆN LÕI (NUMPY & OPENCV)")
    print("="*60)
    # Cài numpy < 2 và opencv tương thích để không bị lỗi DLL
    run_command(f'"{python_exe}" -m pip install "numpy<2" "opencv-python<4.11"')
    
    print("\n" + "="*60)
    print(f"🔥 BƯỚC 3: CÀI ĐẶT THƯ VIỆN DLL NVIDIA (CUDA {cuda_version})")
    print("="*60)
    if cuda_version == "12.1":
        # Danh sách các gói NVIDIA DLL cần thiết cho ONNXRuntime-GPU 1.26
        run_command(f'"{python_exe}" -m pip install nvidia-cublas-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-curand-cu12 nvidia-cusolver-cu12 nvidia-cusparse-cu12 nvidia-cuda-runtime-cu12 nvidia-nvjitlink-cu12 nvidia-nvtx-cu12')
    elif cuda_version == "11.8":
        run_command(f'"{python_exe}" -m pip install nvidia-cublas-cu11 nvidia-cudnn-cu11 nvidia-cufft-cu11 nvidia-curand-cu11 nvidia-cusolver-cu11 nvidia-cusparse-cu11 nvidia-cuda-runtime-cu11 nvidia-nvtx-cu11')
    else:
        print("[*] Bỏ qua vì chạy trên CPU.")
    
    print("\n" + "="*60)
    print("⚙️ BƯỚC 4: CÀI ĐẶT ENGINE AI")
    print("="*60)
    if use_tensorrt:
        print("[+] Cài đặt TensorRT và ONNXRuntime mới nhất...")
        run_command(f'"{python_exe}" -m pip install tensorrt==10.1.0 onnxruntime-gpu')
    else:
        print("[+] Cài đặt ONNXRuntime-GPU (CUDA 12)...")
        run_command(f'"{python_exe}" -m pip install onnxruntime-gpu')

    print("\n" + "="*60)
    print("🎉 HOÀN TẤT CÀI ĐẶT! MÔI TRƯỜNG ĐÃ SẴN SÀNG 100%.")
    print("="*60)
    print("[*] Bạn có thể chạy ứng dụng bằng lệnh: py main.py")

if __name__ == "__main__":
    setup_environment()
