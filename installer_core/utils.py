import sys
import os
import hashlib
import subprocess

if sys.platform == 'win32':
    import ctypes

def hide_console_window():
    if sys.platform == 'win32':
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)

def get_file_hash(filepath):
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

# Đã tách hàm create_desktop_shortcut sang file shortcut.py
