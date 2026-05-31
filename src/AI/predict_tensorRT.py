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
        for p in sys.path:
            if 'site-packages' in p:
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
        self.context.set_input_shape(input_name, x.shape)
        
        # Truyền con trỏ bộ nhớ (pointer) của mảng CuPy trực tiếp cho TensorRT
        self.context.set_tensor_address(input_name, x.data.ptr)
        
        # Cấp phát GPU cho output (dùng CuPy)
        outputs = {}
        for name in self.output_names:
            shape = self.engine.get_tensor_shape(name)
            shape = list(shape)
            for i, s in enumerate(shape):
                if s == -1: shape[i] = x.shape[i] if i < len(x.shape) else 1
                
            out_size = np.prod(shape) * 4 # float32 = 4 bytes
            if name not in self.buffers or self.buffers[name].size * 4 < out_size:
                self.buffers[name] = cp.empty(shape, dtype=cp.float32)
                
            out_array = self.buffers[name].reshape(shape)
            self.context.set_tensor_address(name, out_array.data.ptr)
            outputs[name] = out_array
            
        # Chạy inference trên Stream
        self.context.execute_async_v3(self.stream)
        cudart.cudaStreamSynchronize(self.stream)
        
        # Trả về trực tiếp mảng CuPy, không cần Copy GPU -> CPU!
        logits = outputs.get('logits', outputs.get(self.output_names[0]))
        detections = outputs.get('detections', outputs.get(self.output_names[1]) if len(self.output_names) > 1 else None)
        
        return logits, detections
