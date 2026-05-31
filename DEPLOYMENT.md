# Hướng Dẫn Triển Khai Hệ Thống AI Nhận Diện Biển Số

Hệ thống này được thiết kế với cơ chế **Tự động nhận diện GPU** và **Tự động biên dịch mô hình TensorRT (Engine)**. Bạn có thể dễ dàng sao chép toàn bộ thư mục dự án sang một máy tính Windows khác có card màn hình (NVIDIA GPU) bất kỳ và làm theo hướng dẫn dưới đây.

---

## 1. Cài Đặt Môi Trường Cơ Bản

### Cài đặt Conda và Python
1. Tải và cài đặt **Miniconda** hoặc **Anaconda**.
2. Mở Anaconda Prompt (hoặc Terminal) và tạo môi trường ảo mới:
   ```bash
   conda create -n bgr_ai python=3.12
   conda activate bgr_ai
   ```

### Cài đặt Thư Viện (Pip)
Mở thư mục chứa dự án và chạy lệnh sau để tự động cài toàn bộ thư viện:
```bash
pip install -r requirements.txt
```

> [!WARNING]
> **Lưu ý về phiên bản CUDA:**
> - Mặc định file `requirements.txt` sử dụng thư viện `cupy-cuda12x` (Dành cho máy tính cài **CUDA 12**).
> - Nếu máy tính mới của bạn là máy cũ và chỉ hỗ trợ **CUDA 11**, bạn cần mở file `requirements.txt`, tìm dòng `cupy-cuda12x` và đổi nó thành `cupy-cuda11x` TRƯỚC KHI chạy lệnh `pip install`.

---

## 2. Cơ Chế Khởi Động Tự Động (TensorRT Fallback)

Hệ thống này đã được lập trình sẵn công nghệ **Auto-Build Engine**.
Khi bạn chạy lệnh `python main.py` trên một chiếc máy tính mới, quá trình sau sẽ tự động diễn ra:
1. Hệ thống dùng lệnh nội bộ để truy vấn tên của Card màn hình (Ví dụ: `nvidia_geforce_gtx_1650`).
2. Nó sẽ quét tìm file Engine: `src/models/TensorRT/yolo_rvit_v11s_gru_local_nvidia_geforce_gtx_1650.engine`.
3. Vì là máy mới nên file này chưa tồn tại. Lập tức, hệ thống sẽ kích hoạt file `trt_builder.py` dưới nền, tự động phân tích Card màn hình và **sinh ra một file `.engine` mới tương thích tuyệt đối** với sức mạnh của Card màn hình đó. 
4. Quá trình Build này có thể mất khoảng **2 - 5 phút** cho lần chạy đầu tiên. Kể từ lần thứ 2 trở đi, nó sẽ tải thẳng file Engine đã lưu và khởi động ngay lập tức (Thời gian load chưa tới 1 giây).
5. Nếu quá trình Build thất bại vì một lý do phần cứng nào đó (như thiếu RAM), hệ thống sẽ kích hoạt **Safety Net Fallback** và tự động lùi về sử dụng mô hình ONNX để đảm bảo luồng xử lý không bao giờ bị sập.

---

## 3. Tối Ưu Hóa Hiệu Năng (Sửa lỗi rớt FPS)

Nếu máy tính mới xử lý Inference không ổn định (thời gian Inference đôi lúc nhảy vọt từ 5ms lên 20ms-30ms), đó **KHÔNG PHẢI** là lỗi phần mềm. Đó là do tính năng Tiết Kiệm Điện (P-State Throttling) của NVIDIA tự động hạ xung nhịp (Clock) khi GPU rảnh rỗi.

Để khóa cứng sức mạnh của GPU ở trạng thái tối đa (giúp FPS ổn định ở mốc 100+), hãy làm 1 trong 2 cách sau:

### Cách 1: Dùng NVIDIA Control Panel (Đề xuất)
1. Chuột phải ở Desktop -> Chọn **NVIDIA Control Panel**.
2. Chọn **Manage 3D settings**.
3. Cuộn xuống tìm **Power management mode** -> Chuyển thành **Prefer maximum performance**.
4. Bấm Apply.

### Cách 2: Dùng lệnh ép xung (Dành cho máy Server/Máy không có giao diện)
1. Mở Command Prompt bằng quyền **Administrator**.
2. Kiểm tra xung nhịp tối đa của Card màn hình bằng lệnh:
   ```bash
   nvidia-smi -q -d CLOCK
   ```
   *Nhìn vào mục `Max Clocks -> Graphics` (Ví dụ 2115 MHz).*
3. Khóa xung nhịp bằng lệnh sau:
   ```bash
   nvidia-smi -lgc <MAX_CLOCK>,<MAX_CLOCK>
   # Ví dụ với mốc 2115 MHz:
   nvidia-smi -lgc 2115,2115
   ```
*(Nếu muốn hủy ép xung, bạn dùng lệnh `nvidia-smi -rgc`)*.

---

Dự án này đã được tối ưu Memory Buffer bằng CuPy và CUDA Graphs tĩnh hóa, đảm bảo khả năng đáp ứng cho luồng video Real-time lên tới 100 FPS hoàn toàn ổn định trên các nền tảng Python 3.x!
