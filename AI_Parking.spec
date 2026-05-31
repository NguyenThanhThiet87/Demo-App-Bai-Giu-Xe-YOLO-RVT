# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('src/models/ONNX', 'src/models/ONNX')]
binaries = [('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cublas\\bin', 'nvidia/cublas/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cuda_nvrtc\\bin', 'nvidia/cuda_nvrtc/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cuda_runtime\\bin', 'nvidia/cuda_runtime/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cudnn\\bin', 'nvidia/cudnn/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cufft\\bin', 'nvidia/cufft/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\curand\\bin', 'nvidia/curand/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cusolver\\bin', 'nvidia/cusolver/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\cusparse\\bin', 'nvidia/cusparse/bin'), ('C:\\Users\\Administrator\\Downloads\\app\\Demo-App-Bai-Giu-Xe-YOLO-RVT\\.venv\\Lib\\site-packages\\nvidia\\nvjitlink\\bin', 'nvidia/nvjitlink/bin')]
hiddenimports = ['tensorrt', 'graphlib', 'cv2', 'pymongo', 'PySide6']
tmp_ret = collect_all('cupy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cupy_backends')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('cupyx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='AI_Parking',
)
