import sys
import io

# Thiết lập stdout và stderr sang UTF-8 để tránh lỗi mã hóa trên Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from TRTUtils import TensorRTConverter

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    path_onnx = sys.argv[1]
    path_model = sys.argv[2]

    try:
        converter = TensorRTConverter()
        if not converter.check_engine_compatibility(path_model):
            print("[*] Phát hiện engine không tương thích. Đang tiến hành build lại cho GPU này...")
            success = converter.convert_onnx_to_engine(path_onnx, path_model)
            if not success:
                sys.exit(1)
        else:
            print("[*] Engine TensorRT đã sẵn sàng sử dụng.")
    except Exception as e:
        print(f"[-] Lỗi TensorRT trong quá trình xử lý: {e}")
        sys.exit(1)
