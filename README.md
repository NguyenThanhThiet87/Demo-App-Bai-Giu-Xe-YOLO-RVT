<div align="center">

# 🚗 AI Parking Management System

<img width="895" height="567" alt="AI Parking System" src="https://github.com/user-attachments/assets/917624cd-52ef-4ee9-b5ae-4d08b4f8f6e3" />

![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue)
![YOLO](https://img.shields.io/badge/AI-YOLO-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![GPU](https://img.shields.io/badge/GPU-NVIDIA-success)

**Hệ thống quản lý bãi đỗ xe thông minh ứng dụng AI nhận diện biển số xe bằng YOLO.**

Được đóng gói kèm trình cài đặt tự động, cho phép người dùng khởi chạy hệ thống chỉ với vài thao tác đơn giản mà không cần cài đặt Python hay cấu hình môi trường thủ công.

</div>

---

## 📖 Tổng Quan

AI Parking Management System là giải pháp quản lý bãi đỗ xe sử dụng công nghệ Computer Vision và Deep Learning để tự động phát hiện và nhận diện biển số xe theo thời gian thực.

### Tính năng chính

* 🚘 Nhận diện biển số xe bằng YOLO
* ⚡ Xử lý thời gian thực với FPS cao
* 🖥️ Giao diện trực quan, dễ sử dụng
* 📦 Trình cài đặt tự động cho người dùng cuối
* 🪟 Hỗ trợ Windows
* 🐧 Hỗ trợ Linux

---

## 🎥 Demo Input Videos

Bộ video dùng để kiểm thử và đánh giá hệ thống được cung cấp tại:

🔗 **Google Drive Folder**

https://drive.google.com/drive/folders/1fYgxYnRbZ4w0RkxoaissDj2lD6Jt09S2?usp=drive_link

Các video này có thể được sử dụng làm dữ liệu đầu vào để:

* Kiểm thử chức năng hệ thống
* Đánh giá độ chính xác nhận diện
* Đo hiệu năng xử lý
* Trình diễn sản phẩm

---

## 🚀 Quick Start

### 🪟 Windows

1. Mở thư mục dự án.
2. Chạy file:

```bash
run_app.bat
```

3. Trình cài đặt sẽ tự động:

   * Kiểm tra môi trường
   * Tải các thư viện cần thiết
   * Cấu hình hệ thống

4. Sau khi hoàn tất, ứng dụng sẽ tự động khởi động.

---

### 🐧 Linux (Ubuntu / Debian)

Mở Terminal tại thư mục dự án:

```bash
chmod +x run_app.sh
./run_app.sh
```

Hệ thống sẽ tự động cài đặt các thành phần cần thiết và khởi chạy ứng dụng.

---

## ⚡ Các Lần Khởi Chạy Tiếp Theo

Sau lần cài đặt đầu tiên, hệ thống sẽ tạo shortcut:

```text
AI Parking
```

trên Desktop.

Từ những lần sử dụng tiếp theo, chỉ cần nhấp đúp vào biểu tượng này để mở ứng dụng mà không cần thực hiện lại quá trình cài đặt.

> Nếu shortcut bị xóa, chỉ cần chạy lại `run_app.bat` để hệ thống tự động tạo lại.

---

## 🛠️ Cấu Trúc Dự Án

```text
.
├── app/                # Source code chính
├── installer_core/     # Trình cài đặt tự động
├── logo/               # Logo và icon
├── run_app.bat         # Launcher cho Windows
└── run_app.sh          # Launcher cho Linux
```

### Mô tả

| Thư mục           | Chức năng                                               |
| ----------------- | ------------------------------------------------------- |
| `app/`            | Chứa giao diện PySide6, mô hình YOLO và logic nghiệp vụ |
| `installer_core/` | Chứa bộ cài đặt tự động và cơ chế kiểm tra môi trường   |
| `logo/`           | Chứa logo và icon desktop                               |
| `run_app.bat`     | Điểm khởi động trên Windows                             |
| `run_app.sh`      | Điểm khởi động trên Linux                               |

---

## 📊 Performance Benchmark

### Inference Performance

| Device                        |     Pre | Inference |    Post | Display |    Total |     FPS |
| :---------------------------- | ------: | --------: | ------: | ------: | -------: | ------: |
| NVIDIA RTX 3060 (12GB VRAM)   | 1.66 ms |   4.87 ms | 0.53 ms | 1.49 ms |  8.55 ms | **116** |
| NVIDIA RTX 3050 Ti (4GB VRAM) | 1.57 ms |  12.92 ms | 0.32 ms | 1.47 ms | 16.28 ms |  **62** |

> Benchmark được đo trên pipeline hoàn chỉnh bao gồm tiền xử lý (Pre-processing), suy luận mô hình (Inference), hậu xử lý (Post-processing) và hiển thị kết quả (Display).

---

## 📄 License

Dự án được phát triển phục vụ mục đích học tập, nghiên cứu và trình diễn công nghệ AI trong quản lý bãi đỗ xe.
