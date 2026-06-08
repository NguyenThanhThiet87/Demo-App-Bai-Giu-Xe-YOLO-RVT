#!/bin/bash
# AI Parking - Auto Installer & Runner for Linux

# Lấy thư mục hiện tại của script
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
MINICONDA_DIR="$BASE_DIR/miniconda"
PYTHON_EXE="$MINICONDA_DIR/bin/python"

echo "===================================================================="
echo "            AI PARKING MANAGEMENT SYSTEM - KHỞI ĐỘNG TỰ ĐỘNG"
echo "===================================================================="
echo ""

# 1. Kiểm tra nếu môi trường miniconda đã tồn tại
if [ -f "$PYTHON_EXE" ]; then
    echo "[+] Đã tìm thấy môi trường Python cục bộ."
else
    echo "[-] Chưa có môi trường Python cục bộ. Đang bắt đầu thiết lập..."
    echo "[*] Đang tải xuống Miniconda (khoảng 70MB)..."
    
    if command -v curl &> /dev/null; then
        curl -sL "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" -o miniconda_installer.sh
    elif command -v wget &> /dev/null; then
        wget -q "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh" -O miniconda_installer.sh
    else
        echo "[!] Lỗi: Không tìm thấy 'curl' hoặc 'wget' để tải file."
        exit 1
    fi
    
    if [ ! -f "miniconda_installer.sh" ]; then
        echo "[!] Lỗi: Không thể tải xuống Miniconda."
        exit 1
    fi
    
    echo "[*] Đang cài đặt Miniconda âm thầm vào thư mục: $MINICONDA_DIR"
    bash miniconda_installer.sh -b -p "$MINICONDA_DIR"
    rm miniconda_installer.sh
    
    if [ ! -f "$PYTHON_EXE" ]; then
        echo "[!] Lỗi: Cài đặt Miniconda thất bại."
        exit 1
    fi
    
    echo "[+] Cài đặt Miniconda thành công!"
fi

echo "[*] Đang khởi chạy Giao diện Cài đặt / Ứng dụng..."
cd "$BASE_DIR"

# Kiểm tra nếu trên Linux có cài đặt tkinter (python3-tk) chưa
# (Trên Windows nó được tích hợp sẵn, trên Linux thì đôi khi cần cài riêng, 
# tuy nhiên bản Python của Miniconda đã thường có sẵn tk)

"$PYTHON_EXE" gui_installer.py
if [ $? -ne 0 ]; then
    echo "[!] Ứng dụng đã dừng lại với lỗi."
fi
