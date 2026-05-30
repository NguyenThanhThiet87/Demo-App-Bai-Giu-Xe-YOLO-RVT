import os
import sys
import numpy as np
import ctypes

# Lazy import tensorrt để tránh lỗi C++ conflict với ONNXRuntime

# Nạp thư viện CUDA Runtime
cudart = None
try:
    # Tìm cudart64_110.dll trong PATH (chúng ta đã thêm nó trong main/predict)
    cudart = ctypes.CDLL('cudart64_110.dll')
    cudart.cudaMalloc.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_size_t]
    cudart.cudaMemcpy.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
    cudart.cudaFree.argtypes = [ctypes.c_void_p]
    cudart.cudaStreamCreate.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
    cudart.cudaStreamSynchronize.argtypes = [ctypes.c_void_p]
    
    cudaMemcpyHostToDevice = 1
    cudaMemcpyDeviceToHost = 2
except Exception as e:
    print(f"Warning: cudart64_110.dll không được nạp. Lỗi: {e}")

class TRTEngineWrapper:
    def __init__(self, engine_path):
        if cudart is None:
            raise RuntimeError("Thiếu thư viện CUDA C++ (cudart64_110.dll).")
            
        import tensorrt as trt
        self.logger = trt.Logger(trt.Logger.WARNING)
        with open(engine_path, "rb") as f, trt.Runtime(self.logger) as runtime:
            self.engine = runtime.deserialize_cuda_engine(f.read())
        
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
        # x là numpy array từ preprocess (CPU)
        if not isinstance(x, np.ndarray):
            x = np.array(x, dtype=np.float32)
        if x.dtype != np.float32:
            x = x.astype(np.float32)
            
        input_name = self.input_names[0]
        self.context.set_input_shape(input_name, x.shape)
        
        # Cấp phát GPU cho input nếu chưa có hoặc kích thước đổi
        input_size = x.nbytes
        if input_name not in self.buffers or self.buffers[input_name][1] < input_size:
            if input_name in self.buffers:
                cudart.cudaFree(self.buffers[input_name][0])
            ptr = ctypes.c_void_p()
            cudart.cudaMalloc(ctypes.byref(ptr), input_size)
            self.buffers[input_name] = (ptr.value, input_size)
            
        # Copy numpy (CPU) -> GPU (Input)
        cudart.cudaMemcpy(self.buffers[input_name][0], x.ctypes.data_as(ctypes.c_void_p), input_size, cudaMemcpyHostToDevice)
        self.context.set_tensor_address(input_name, self.buffers[input_name][0])
        
        # Cấp phát GPU cho output
        outputs = {}
        for name in self.output_names:
            shape = self.engine.get_tensor_shape(name)
            shape = list(shape)
            for i, s in enumerate(shape):
                if s == -1: shape[i] = x.shape[i] if i < len(x.shape) else 1
                
            out_size = np.prod(shape) * 4 # float32 = 4 bytes
            if name not in self.buffers or self.buffers[name][1] < out_size:
                if name in self.buffers:
                    cudart.cudaFree(self.buffers[name][0])
                ptr = ctypes.c_void_p()
                cudart.cudaMalloc(ctypes.byref(ptr), out_size)
                self.buffers[name] = (ptr.value, out_size)
                
            self.context.set_tensor_address(name, self.buffers[name][0])
            outputs[name] = np.empty(shape, dtype=np.float32)
            
        # Chạy inference trên Stream
        self.context.execute_async_v3(self.stream)
        cudart.cudaStreamSynchronize(self.stream)
        
        # Copy GPU -> numpy (CPU)
        for name in self.output_names:
            out_size = outputs[name].nbytes
            cudart.cudaMemcpy(outputs[name].ctypes.data_as(ctypes.c_void_p), self.buffers[name][0], out_size, cudaMemcpyDeviceToHost)
            
        logits = outputs.get('logits', outputs.get(self.output_names[0]))
        detections = outputs.get('detections', None)
        
        return logits, detections
