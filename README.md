# 🚗 AI Parking Management System
<img width="895" height="567" alt="image" src="https://github.com/user-attachments/assets/917624cd-52ef-4ee9-b5ae-4d08b4f8f6e3" />

Chào mừng bạn đến với Hệ thống Quản lý Bãi đỗ xe thông minh ứng dụng AI (nhận diện biển số với YOLO). Phần mềm đã được đóng gói kèm theo Trình Cài Đặt Tự Động cực kỳ tiện lợi, giúp bạn khởi chạy ứng dụng chỉ với 1 cú click chuột mà không cần biết về lập trình hay thao tác dòng lệnh.

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Phần Mềm

Máy tính của bạn **không cần cài sẵn Python**! Hệ thống sẽ tự động lo liệu tất cả từ A đến Z.

### 🪟 Đối với Windows
1. Mở thư mục chứa mã nguồn.
2. Click đúp chuột vào file **`run_app.bat`**.
3. Một giao diện đồ họa sẽ hiện lên để tự động cài đặt các thư viện AI cần thiết (chỉ tải ở lần đầu tiên).
4. Đợi cài đặt hoàn tất, phần mềm AI Parking sẽ tự động mở lên!

### 🐧 Đối với Linux (Ubuntu / Debian...)
1. Mở Terminal (Dòng lệnh) tại thư mục chứa mã nguồn.
2. Cấp quyền thực thi cho script: `chmod +x run_app.sh`
3. Chạy script: `./run_app.sh`
4. Quá trình cài đặt thư viện và mở ứng dụng sẽ diễn ra tự động.

---

## ✨ Những Lần Chạy Tiếp Theo (Rất Nhanh)

Sau khi cài đặt thành công lần đầu tiên, hệ thống sẽ tự động tạo một **Biểu tượng (Shortcut) mang tên "AI Parking"** ngay trên màn hình **Desktop** của bạn.

Từ những lần sau, bạn **chỉ cần ra ngoài màn hình Desktop và click đúp vào Icon AI Parking** là phần mềm sẽ ngay lập tức được mở lên (hiển thị luôn màn hình chờ tải AI) mà không qua bước cài đặt nữa. 

*(Lưu ý: Nếu bạn vô tình xóa mất Icon ngoài Desktop, chỉ cần quay lại thư mục gốc và chạy file `run_app.bat` một lần nữa, Icon sẽ tự động được khôi phục).*

---

## 🛠️ Cấu Trúc Dự Án Dành Cho Lập Trình Viên (Dễ Bảo Trì)

Nếu bạn là nhà phát triển muốn xem mã nguồn, dự án được tổ chức rất rõ ràng:
- **`app/`**: Thư mục chứa toàn bộ Source Code chính của phần mềm AI Parking (Giao diện PySide6, Mô hình YOLO, v.v).
- **`installer_core/`**: Thư mục chứa Source Code của bộ Trình Cài Đặt Tự Động (Giao diện Tkinter, check hash, v.v).
- **`logo/`**: Nơi chứa hình ảnh Logo cho biểu tượng Desktop.
- **`run_app.bat` / `run_app.sh`**: File "mồi" để khởi động trình cài đặt.

## Performance Benchmark

| Device | Pre | Inference | Post | Display | Total | FPS |
|----------|----------|----------|----------|----------|----------|----------|
| NVIDIA RTX 3060 (12GB VRAM) | 1.66 ms | 4.87 ms | 0.53 ms | 1.49 ms | 8.55 ms | 116 |
| NVIDIA RTX 3050 Ti (4GB VRAM) | 1.57 ms | 12.92 ms | 0.32 ms | 1.47 ms | 16.28 ms | 62 |
