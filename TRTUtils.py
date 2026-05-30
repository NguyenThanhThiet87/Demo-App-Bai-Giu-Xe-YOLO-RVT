import sys
import os

try:
    if getattr(sys, 'frozen', False):
        os.add_dll_directory(sys._MEIPASS)
    import tensorrt as trt
    TRT_AVAILABLE = True
except Exception as e:
    print(f"[!] Lỗi khi nạp TensorRT: {e}")
    TRT_AVAILABLE = False

class TensorRTConverter:
    def __init__(self):
        if not TRT_AVAILABLE:
            self.logger = None
        else:
            self.logger = trt.Logger(trt.Logger.WARNING)

    def convert_onnx_to_engine(self, onnx_file_path, engine_file_path, fp16_mode=True):
        """
        Chuyển đổi file ONNX sang TensorRT Engine phù hợp với GPU hiện tại.
        """
        if not os.path.exists(onnx_file_path):
            print(f"[-] Lỗi: Không tìm thấy file ONNX tại {onnx_file_path}")
            return False

        print(f"[*] Đang bắt đầu chuyển đổi: {onnx_file_path} -> {engine_file_path}")
        
        # 1. Khởi tạo builder và network
        builder = trt.Builder(self.logger)
        
        # Xử lý tương thích cho TensorRT 10+ (EXPLICIT_BATCH đã bị xóa vì trở thành mặc định)
        if hasattr(trt.NetworkDefinitionCreationFlag, 'EXPLICIT_BATCH'):
            network_flags = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        else:
            network_flags = 0
            
        network = builder.create_network(network_flags)
        parser = trt.OnnxParser(network, self.logger)
        config = builder.create_builder_config()
        
        # Thiết lập bộ nhớ đệm (Workspace size) - ví dụ 1GB
        config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)

        # 2. Parse file ONNX
        if not parser.parse_from_file(onnx_file_path):
            for error in range(parser.num_errors):
                print(f"[!] ONNX Parse Error: {parser.get_error(error)}")
            return False

        # 3. Cấu hình chế độ FP16 (nếu GPU hỗ trợ) để tăng tốc độ
        if fp16_mode:
            if builder.platform_has_fast_fp16:
                config.set_flag(trt.BuilderFlag.FP16)
                print("[+] GPU hỗ trợ chế độ FP16 - Đã kích hoạt tối ưu hóa.")
            else:
                print("[!] GPU không hỗ trợ FP16 nhanh - Chuyển về FP32.")

        # 4. Build Engine
        print("[*] Đang build engine (quá trình này có thể mất vài phút)...")
        serialized_engine = builder.build_serialized_network(network, config)
        
        if serialized_engine is None:
            print("[!] Lỗi: Không thể build engine.")
            return False

        # 5. Lưu engine ra file
        with open(engine_file_path, 'wb') as f:
            f.write(serialized_engine)
        
        print(f"[+] Thành công! Engine đã được lưu tại: {engine_file_path}")
        return True

    def check_engine_compatibility(self, engine_file_path):
        """
        Kiểm tra xem file engine hiện tại có tương thích với GPU này không.
        """
        if not os.path.exists(engine_file_path):
            return False
            
        runtime = trt.Runtime(self.logger)
        try:
            with open(engine_file_path, 'rb') as f:
                engine_data = f.read()
                # Thử deserialize engine
                engine = runtime.deserialize_cuda_engine(engine_data)
                if engine:
                    print(f"[+] File engine {os.path.basename(engine_file_path)} tương thích hoàn toàn với GPU này.")
                    return True
        except Exception as e:
            print(f"[!] File engine không tương thích hoặc bị lỗi: {str(e)}")
            
        return False

