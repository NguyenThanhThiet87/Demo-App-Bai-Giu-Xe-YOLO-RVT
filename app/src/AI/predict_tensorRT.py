import os
import sys
import numpy as np
import ctypes

# Lazy import tensorrt để tránh lỗi C++ conflict với ONNXRuntime

# Nạp thư viện CUDA Runtime
cudart = None
cuda_dlls = ['cudart64_12.dll', 'cudart64_110.dll', 'cudart64_100.dll']
for dll_name in cuda_dlls:
    try:
        cudart = ctypes.CDLL(dll_name)
        print(f"[+] Loaded CUDA runtime DLL: {dll_name}")
        break
    except Exception:
        continue

if cudart is None:
    try:
        # Tạo danh sách đường dẫn cần quét
        search_paths = list(sys.path)
        
        # Khi chạy dưới dạng .exe (frozen), thêm thư mục _internal vào danh sách quét
        if getattr(sys, 'frozen', False):
            _exe_dir = os.path.dirname(sys.executable)
            _internal_dir = os.path.join(_exe_dir, '_internal')
            search_paths = [_internal_dir, _exe_dir] + search_paths
            
            # Thử load trực tiếp từ _internal trước
            for f in os.listdir(_internal_dir) if os.path.exists(_internal_dir) else []:
                if f.startswith('cudart64_') and f.endswith('.dll'):
                    try:
                        cudart = ctypes.CDLL(os.path.join(_internal_dir, f))
                        print(f"[+] Loaded CUDA runtime DLL from _internal: {f}")
                        break
                    except Exception:
                        pass

        if cudart is None:
            for p in search_paths:
                if 'site-packages' in p or getattr(sys, 'frozen', False):
                    rt_dir = os.path.join(p, 'nvidia', 'cuda_runtime', 'bin')
                    if os.path.exists(rt_dir):
                        for f in os.listdir(rt_dir):
                            if f.startswith('cudart64_') and f.endswith('.dll'):
                                try:
                                    cudart = ctypes.CDLL(os.path.join(rt_dir, f))
                                    print(f"[+] Loaded CUDA runtime DLL from site-packages: {f}")
                                    break
                                except Exception:
                                    pass
                        if cudart:
                            break
    except Exception as scan_err:
        print(f"[-] Quét tìm cudart64 failed: {scan_err}")


if cudart is not None:
    try:
        cudart.cudaMalloc.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
        cudart.cudaMemcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
        cudart.cudaFree.argtypes = [ctypes.c_void_p]
        cudart.cudaStreamCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        cudart.cudaStreamSynchronize.argtypes = [ctypes.c_void_p]
        
        # Hàm cấu hình CUDA Graph
        cudart.cudaStreamBeginCapture.argtypes = [ctypes.c_void_p, ctypes.c_int]
        cudart.cudaStreamEndCapture.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        cudart.cudaGraphInstantiate.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
        cudart.cudaGraphLaunch.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cudart.cudaGraphExecDestroy.argtypes = [ctypes.c_void_p]
        cudart.cudaGraphDestroy.argtypes = [ctypes.c_void_p]
        
        cudaMemcpyHostToDevice = 1
        cudaMemcpyDeviceToHost = 2
    except Exception as e:
        print(f"Warning: Lỗi thiết lập các hàm CUDA runtime. Lỗi: {e}")
        cudart = None
else:
    print("[-] Lỗi: Không thể tìm thấy hoặc nạp bất kỳ thư viện cudart64 nào!")

class TRTEngineWrapper:
    def __init__(self, engine_path):
        if cudart is None:
            raise RuntimeError("Thiếu thư viện CUDA C++ (cudart64).")
            
        import tensorrt as trt
        self.logger = trt.Logger(trt.Logger.WARNING)
        with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
        if self.engine is None:
            raise RuntimeError(f"Không thể deserialize CUDA engine từ {engine_path}. Hãy kiểm tra tính tương thích của GPU và phiên bản TensorRT.")
            
        self.context = self.engine.create_execution_context()
        self.trt = trt
        
        # Tạo CUDA stream
        stream_ptr = ctypes.c_void_p()
        cudart.cudaStreamCreate(ctypes.byref(stream_ptr))
        self.stream = stream_ptr.value
        
        # Lấy tên các tensor
        self.input_names = []
        self.output_names = []
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            if self.engine.get_tensor_mode(name) == self.trt.TensorIOMode.INPUT:
                self.input_names.append(name)
            else:
                self.output_names.append(name)
        
        # Cấp phát bộ nhớ
        self.buffers = {}
        
        # Cấu trúc cho CUDA Graph
        self.graph_exec = None
        self.static_input_shape = None
        self.static_input_buffer = None
        
        print(f"Loaded TRT Engine: {engine_path}")
        print(f"Inputs: {self.input_names}")
        print(f"Outputs: {self.output_names}")

    def __call__(self, x):
        import cupy as cp
        # x là cupy array từ preprocess (GPU)
        if not isinstance(x, cp.ndarray):
            x = cp.asarray(x, dtype=cp.float32)
        if x.dtype != cp.float32:
            x = x.astype(cp.float32)
        x = cp.ascontiguousarray(x)
            
        input_name = self.input_names[0]
        
        # --- CƠ CHẾ SAFETY NET CHO CUDA GRAPHS ---
        # Kiểm tra xem shape có bị đổi so với graph cũ không
        if self.static_input_shape is not None and x.shape != self.static_input_shape:
            # Nếu đổi shape, hủy graph cũ đi để tạo lại
            if self.graph_exec is not None:
                cudart.cudaGraphExecDestroy(self.graph_exec)
                self.graph_exec = None
            self.static_input_shape = None
            self.static_input_buffer = None
            print(f"[!] Cảnh báo: Kích thước đầu vào bị thay đổi thành {x.shape}. Hủy CUDA Graph cũ.")

        # Cấp phát mảng tĩnh một lần duy nhất
        if self.static_input_shape is None:
            self.static_input_shape = x.shape
            self.static_input_buffer = cp.empty_like(x)
            
        # Cấp phát mảng tĩnh cho outputs
        outputs = {}
        for name in self.output_names:
            shape = self.engine.get_tensor_shape(name)
            shape = list(shape)
            for i, s in enumerate(shape):
                if s == -1: shape[i] = x.shape[i] if i < len(x.shape) else 1
                
            out_size = np.prod(shape) * 4 # float32 = 4 bytes
            if name not in self.buffers or self.buffers[name].size * 4 < out_size:
                self.buffers[name] = cp.empty(shape, dtype=cp.float32)
            outputs[name] = self.buffers[name].reshape(shape)

        # 1. Copy dữ liệu mới vào mảng tĩnh (giữ nguyên địa chỉ RAM)
        cp.copyto(self.static_input_buffer, x)
        
        # --- THỰC THI (GRAPH HOẶC THÔNG THƯỜNG) ---
        if self.graph_exec is None:
            # Lần chạy đầu tiên: Gán địa chỉ tĩnh và Bắt giữ đồ thị (Capture)
            self.context.set_input_shape(input_name, self.static_input_shape)
            self.context.set_tensor_address(input_name, self.static_input_buffer.data.ptr)
            for name in self.output_names:
                self.context.set_tensor_address(name, outputs[name].data.ptr)
                
            # Bắt đầu quay phim (Capture) - mode = 0 (Global)
            cudart.cudaStreamBeginCapture(self.stream, 0)
            
            # Chạy hàm inference thông thường để GPU ghi nhận lệnh
            self.context.execute_async_v3(self.stream)
            
            # Kết thúc quay phim và lưu graph
            graph = ctypes.c_void_p()
            cudart.cudaStreamEndCapture(self.stream, ctypes.byref(graph))
            
            # Biến bản vẽ thành Graph Executable
            graph_exec = ctypes.c_void_p()
            ret = cudart.cudaGraphInstantiate(ctypes.byref(graph_exec), graph, None, None, 0)
            if ret == 0 and graph_exec.value is not None:
                self.graph_exec = graph_exec
                print(f"[+] CUDA Graph đã được ghi nhận thành công ({self.static_input_shape})!")
                # Lệnh execute_async_v3 ở trên chỉ là "ghi âm" chứ không chạy thật.
                # Do đó, ta phải Launch Graph ngay lập tức để Frame đầu tiên có kết quả thay vì trả về mảng rỗng (rác/NaN).
                cudart.cudaGraphLaunch(self.graph_exec, self.stream)
            else:
                print(f"[-] Lỗi khi Instantiate CUDA Graph (mã lỗi: {ret}). Fallback về chạy thường.")
                # Nếu ghi hình lỗi, chạy lại lệnh bình thường
                self.context.execute_async_v3(self.stream)
                
            cudart.cudaGraphDestroy(graph)
            
            # Đảm bảo lệnh inference vừa khởi chạy đã xong cho frame đầu tiên
            cudart.cudaStreamSynchronize(self.stream)
        else:
            # Các frame tiếp theo: Bỏ qua mọi bước CPU, phóng trực tiếp Graph đã ghi nhớ!
            cudart.cudaGraphLaunch(self.graph_exec, self.stream)
            cudart.cudaStreamSynchronize(self.stream)
        
        # Trả về kết quả
        logits = outputs.get('logits', outputs.get(self.output_names[0]))
        detections = outputs.get('detections', outputs.get(self.output_names[1]) if len(self.output_names) > 1 else None)
        
        return logits, detections
