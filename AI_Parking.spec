# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cublas\\bin', 'nvidia/cublas/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cuda_nvrtc\\bin', 'nvidia/cuda_nvrtc/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cuda_runtime\\bin', 'nvidia/cuda_runtime/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cudnn\\bin', 'nvidia/cudnn/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cufft\\bin', 'nvidia/cufft/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\curand\\bin', 'nvidia/curand/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cusolver\\bin', 'nvidia/cusolver/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cusparse\\bin', 'nvidia/cusparse/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\nvjitlink\\bin', 'nvidia/nvjitlink/bin')],
    datas=[('src/models/ONNX', 'src/models/ONNX')],
    hiddenimports=['tensorrt', 'cupy', 'cv2', 'pymongo', 'PySide6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_Parking',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='AI_Parking',
)
