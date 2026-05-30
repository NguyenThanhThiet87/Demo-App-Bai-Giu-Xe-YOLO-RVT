import sys
import os

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

import onnxruntime as ort

print("Available:", ort.get_available_providers())
try:
    session = ort.InferenceSession("D:\\AppBaiDoXe-YOLO_RVT\\AppBaiDoXe-YOLO_RVT\\src\\models\\ONNX\\yolo_rvit_full.onnx", providers=['CUDAExecutionProvider'])
    print("Used:", session.get_providers())
except Exception as e:
    import traceback
    traceback.print_exc()
