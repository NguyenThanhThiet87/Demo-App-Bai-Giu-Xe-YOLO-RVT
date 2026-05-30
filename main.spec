# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob

sys.setrecursionlimit(20000)
site_packages = r"D:/AppBaiDoXe-YOLO_RVT/AppBaiDoXe-YOLO_RVT/.venv/Lib/site-packages"

raw_datas = [
    ('src', 'src'),
    ('untitled.ui', '.'),
    ('.env', '.'),
    ('trt_builder.py', '.'),
    ('TRTUtils.py', '.'),
    ('LicensePlateTracker.py', '.'),
    ('UI.py', '.'),
    ('utils_path.py', '.'),
    ('database.py', '.'),
    ('ui_untitled.py', '.'),
    (os.path.join(site_packages, 'onnxruntime'), 'onnxruntime'),
]

raw_binaries = []

# Nhặt toàn bộ DLL từ nvidia packages
for p in sys.path:
    if 'site-packages' in p:
        nvidia_dir = os.path.join(p, 'nvidia')
        if os.path.exists(nvidia_dir):
            for sub in os.listdir(nvidia_dir):
                bin_dir = os.path.join(nvidia_dir, sub, 'bin')
                if os.path.exists(bin_dir):
                    for dll_path in glob.glob(os.path.join(bin_dir, "*.dll")):
                        raw_binaries.append((dll_path, '.'))
        
        # Nạp thêm TensorRT DLL
        scripts_dir = os.path.join(p, '..', '..', 'Scripts')
        if os.path.exists(scripts_dir):
            for dll_path in glob.glob(os.path.join(scripts_dir, "nv*.dll")) + \
                            glob.glob(os.path.join(scripts_dir, "zlibwapi.dll")):
                raw_binaries.append((dll_path, '.'))
                
        # Nạp thêm TensorRT DLL từ tensorrt_libs (phiên bản mới của pip)
        trt_libs_dir = os.path.join(p, 'tensorrt_libs')
        if os.path.exists(trt_libs_dir):
            for dll_path in glob.glob(os.path.join(trt_libs_dir, "*.dll")):
                raw_binaries.append((dll_path, '.'))

valid_datas = []
for src, dst in raw_datas:
    if os.path.exists(src):
        valid_datas.append((src, dst))
    else:
        print(f"[WARNING] File/thư mục không tồn tại, bỏ qua: {src}")

valid_binaries = []
for src, dst in raw_binaries:
    if os.path.exists(src):
        # Lọc bỏ các file DLL cũ dư thừa để giảm dung lượng file Setup
        name = os.path.basename(src).lower()
        
        # Bỏ qua CUDA 11 và cuDNN 8 (vì ONNX 1.19.2 dùng CUDA 12 + cuDNN 9)
        if '_11.dll' in name and 'nvinfer' not in name:
            continue
        if '110.dll' in name: # vd: cudart64_110.dll
            continue
        if 'cudnn64_8.dll' in name or 'cudnn_adv_infer64_8.dll' in name or 'cudnn_cnn_infer64_8.dll' in name or 'cudnn_ops_infer64_8.dll' in name:
            continue
        if 'cudnn_adv_train64_8.dll' in name or 'cudnn_cnn_train64_8.dll' in name or 'cudnn_ops_train64_8.dll' in name:
            continue

        # Bỏ qua TensorRT 8 và TensorRT 11 (vì chúng ta chuẩn hoá dùng TensorRT 10)
        if 'nvinfer_8.dll' in name or 'nvinfer_plugin_8.dll' in name or 'nvinfer64_8.dll' in name:
            continue
        if 'nvonnxparser_8.dll' in name or 'nvparsers_8.dll' in name:
            continue
        if 'nvinfer_11.dll' in name or 'nvinfer_plugin_11.dll' in name or 'nvinfer_builder_resource' in name and '11.dll' in name:
            continue

        valid_binaries.append((src, dst))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=valid_binaries,
    datas=valid_datas,
    hiddenimports=[
        'cv2', 'PySide6', 'motor', 'dotenv', 'numpy',
        'typing_extensions', 'timeit', 'sympy', 'networkx', 'filelock', 
        'jinja2', 'fsspec', 'markupsafe', 'requests', 'urllib3',
        'onnxruntime', 'onnxruntime.capi', 'onnxruntime.capi._pybind_state',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySideWebEngine',
        'torch', 'torchvision', 'torchaudio', 'ultralytics',
        'tensorrt',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AppBaiDoXe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
