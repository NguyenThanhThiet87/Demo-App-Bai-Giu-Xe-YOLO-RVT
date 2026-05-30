import site
import os
import glob

# Tự động tìm thư mục site-packages của venv hiện tại
venv_site = os.path.abspath(os.path.join(os.path.dirname(__file__), '.venv', 'Lib', 'site-packages'))
venv_site = venv_site.replace('\\', '/')

spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob

sys.setrecursionlimit(20000)
site_packages = r"{venv_site}"

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
            for dll_path in glob.glob(os.path.join(scripts_dir, "nv*.dll")) + \\
                            glob.glob(os.path.join(scripts_dir, "zlibwapi.dll")):
                raw_binaries.append((dll_path, '.'))

valid_datas = []
for src, dst in raw_datas:
    if os.path.exists(src):
        valid_datas.append((src, dst))
    else:
        print(f"[WARNING] File/thư mục không tồn tại, bỏ qua: {{src}}")

valid_binaries = []
for src, dst in raw_binaries:
    if os.path.exists(src):
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
    hooksconfig={{}},
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
'''

with open('main.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)
print('Tạo main.spec thành công!')
