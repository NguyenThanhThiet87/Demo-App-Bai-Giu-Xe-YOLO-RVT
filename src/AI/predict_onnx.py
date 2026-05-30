import os
import site
import numpy as np
import sys

# --- TỰ ĐỘNG NẠP THƯ VIỆN CUDA ---
try:
    if getattr(sys, 'frozen', False):
        # Khi đóng gói, DLL nằm trực tiếp ở base_dir (sys._MEIPASS hoặc _internal)
        base_dir = sys._MEIPASS
        dll_paths = [base_dir]
    else:
        dll_paths = []
        for p in sys.path:
            if 'site-packages' in p:
                nvidia_dir = os.path.join(p, 'nvidia')
                if os.path.exists(nvidia_dir):
                    for sub in os.listdir(nvidia_dir):
                        bin_dir = os.path.join(nvidia_dir, sub, 'bin')
                        if os.path.exists(bin_dir):
                            dll_paths.append(bin_dir)
    
    for p in dll_paths:
        if os.path.exists(p):
            if p not in os.environ.get('PATH', ''):
                os.environ['PATH'] = p + ';' + os.environ['PATH']
            if hasattr(os, 'add_dll_directory'):
                os.add_dll_directory(p)
except Exception as e:
    print("CUDA Path Warning:", e)

import onnxruntime as ort

class ONNXEngineWrapper:
    def __init__(self, onnx_path):
        # Tự động kích hoạt TensorRT nếu máy có hỗ trợ, nếu không sẽ tự lùi về CUDA, rồi mới đến CPU
        providers = [
            'TensorrtExecutionProvider',
            ('CUDAExecutionProvider', {
                'cudnn_conv_algo_search': 'DEFAULT',
                'arena_extend_strategy': 'kSameAsRequested',
            }),
            'CPUExecutionProvider'
        ]
        
        session_options = ort.SessionOptions()
        session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        
        self.session = ort.InferenceSession(onnx_path, sess_options=session_options, providers=providers)
        self.onnx_path = onnx_path
        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]
        print(f"Loaded ONNX Model: {onnx_path}")

    def __call__(self, x):
        ort_inputs = {self.input_names[0]: x}
        
        try:
            ort_outs = self.session.run(self.output_names, ort_inputs)
        except Exception as e:
            print(f"[ONNX] Lỗi chạy CUDA/cuDNN ({e}). Đang tự động chuyển sang CPU...")
            # Re-initialize session with CPU only to avoid cuDNN crash on fragmented graphs
            # We need the onnx_path to recreate the session. We can get it from self if we store it.
            if not hasattr(self, 'onnx_path'):
                # fallback using private attribute if available
                model_path = getattr(self.session, '_model_path', None)
            else:
                model_path = self.onnx_path
                
            if model_path:
                self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
                ort_outs = self.session.run(self.output_names, ort_inputs)
                print("[ONNX] Đã chạy thành công trên CPU.")
            else:
                raise e

        print("ORT RESULT", ort_outs)

        logits = ort_outs[0]
        detections = ort_outs[1] if len(ort_outs) > 1 else None
        
        return logits, detections