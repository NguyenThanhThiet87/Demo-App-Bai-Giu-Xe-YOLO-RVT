import cv2
import threading
import queue
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import uic
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import sys
from collections import deque
import torch
from LicensePlateTracker import LicensePlateTracker
from Model_YOLO_RVT.PredictModel import predict_license_plate, load_model_for_prediction
from UI import UI

def get_resolution_name(height):
    """Trả về tên độ phân giải dựa vào chiều cao"""
    if height >= 2160:
        return "4K"
    elif height >= 1440:
        return "2K"
    elif height >= 1080:
        return "1080p (Full HD)"
    elif height >= 720:
        return "720p (HD)"
    elif height >= 480:
        return "480p (SD)"
    elif height >= 360:
        return "360p"
    else:
        return f"{height}p"

class SignalEmitter(QObject):
    """Signal emitter để cập nhật UI an toàn từ thread khác"""
    update_frame = pyqtSignal(QPixmap)  # Signal để cập nhật frame
    update_fps = pyqtSignal(float, float, float)       # Signal để cập nhật FPS
    update_result = pyqtSignal(QPixmap, str, float)  # Signal để cập nhật kết quả

class Result:
    def __init__(self, pixmap, license_plate, confidence, timestamp):
        self.pixmap = pixmap
        self.license_plate = license_plate
        self.confidence = confidence
        self.timestamp = timestamp

YOLO_PATH = 'Model_YOLO_RVT\\yolov11s-pytorch-default-v1\\best.pt'
BEST_CONFIDENCE_THRESHOLD = 0.8
MAX_FRAME_HISTORY = 100
MAX_FRAME_STOPPING = 3
IMG_SIZE_MODEL = (640, 640)
FRAME_SIZE = (640, 480)
FPS_CAMERA = 60

class System:
    def __init__(self, path_model):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = load_model_for_prediction(
            checkpoint_path=path_model,
            yolo_base_model_path=YOLO_PATH
        ).to(self.device).eval()

        if self.device.type == 'cuda':
            self.model = self.model.half() # Sử dụng FP16 trên GPU
            torch.backends.cudnn.benchmark = True # Tối ưu hiệu năng cho các kích thước input cố định
            torch.backends.cuda.matmul.allow_tf32 = True # Cho phép sử dụng TensorFloat-32
            print(f"GPU: {torch.cuda.get_device_name(0)}")

        self.window = UI()

        # Signal emitter để cập nhật UI an toàn từ thread khác
        self.signals = SignalEmitter()
        self.signals.update_frame.connect(self._update_frame_ui)
        self.signals.update_fps.connect(self._update_fps_ui)
        self.signals.update_result.connect(self._update_result_ui)

        # Thêm tracker
        self.lp_tracker = LicensePlateTracker(
            iou_threshold=0.1,         # IoU > 0.3 → cùng object
            max_missing_frames=15,     # Giữ bbox trong 15 frames (~0.5s @ 30fps)
        )
        
        # Queue và Event cho threading 
        self.frame_queue = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()

        # Camera (OpenCV)
        self.video_path = None
        self.cap = None
        # Threads
        self.thread_read = None
        self.thread_ai = None

        self.history = deque(maxlen=100)
        self.previousLP = Result(None, None, 0.0, 0.0)

        self.minFPS = 0
        self.maxFPS = 0
        self.minInferenceTime = 0
        self.maxInferenceTime = 0
        self.minSystemTime = 0
        self.maxSystemTime = 0

    def handleVideo(self):
        # Nếu đang chạy thì dừng
        self.stopAll()

        file_path, _ = QFileDialog.getOpenFileName(
            self.window, "Chọn video", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*.*)"
        )
        if not file_path:
            return

        self.video_path = file_path

        print(f"Selected video: {file_path}")

        self.stop_event.clear()
        # Tạo và chạy threads
        self.thread_read = threading.Thread(target=self.thread_read_video, daemon=True)
        self.thread_ai = threading.Thread(target=self.thread_process_ai, daemon=True)
        self.thread_read.start()
        self.thread_ai.start()

    def handleOpenCamera(self):
        self.stopAll()

        self.stop_event.clear()
        # Tạo và chạy threads
        self.thread_read = threading.Thread(target=self.thread_read_camera, daemon=True)
        self.thread_ai = threading.Thread(target=self.thread_process_ai, daemon=True)
        self.thread_read.start()
        self.thread_ai.start()

    def stopAll(self):
        # Báo hiệu dừng threads
        self.stop_event.set()

        # Đợi threads kết thúc
        if self.thread_read is not None and self.thread_read.is_alive():
            self.thread_read.join(timeout=2)
        if self.thread_ai is not None and self.thread_ai.is_alive():
            self.thread_ai.join(timeout=2)

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Clear queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

        self.window.lblScreen.clear()

    def thread_read_video(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            print(f"[Thread Video] Cannot open video: {self.video_path}")
            self.stop_event.set()
            return

        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Lấy độ phân giải gốc của video
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        resolution_name = get_resolution_name(video_height)
        self.window.setDoPhanGiai(f"{resolution_name} ({video_fps:.2f} FPS)")

        # Giới hạn FPS (giống camera)
        target_fps = min(video_fps, FPS_CAMERA)
        frame_delay = 1.0 / target_fps
        
        print(f"[Thread Video] Video: {total_frames} frames, {video_fps:.2f} FPS (limited to {target_fps:.0f} FPS)")

        while not self.stop_event.is_set():
            frame_start = time.perf_counter()
            
            ret, frame = cap.read()
            if not ret:
                break

            # Resize cho display (giữ lại để hiển thị)
            frame_display = cv2.resize(frame, FRAME_SIZE, interpolation=cv2.INTER_LINEAR)
            frame_display = cv2.cvtColor(frame_display, cv2.COLOR_BGR2RGB)
            
            # Giữ frame gốc BGR cho model (GPU sẽ xử lý resize và BGR->RGB)
            frame_bgr = frame

            # Vứt bỏ frame cũ nếu queue đầy
            if not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Nhét frame BGR và RGB vào queue (tuple: (bgr, rgb_for_display))
            self.frame_queue.put((frame_bgr, frame_display))

            # Giới hạn tốc độ đọc frame mô phỏng FPS camera
            elapsed = time.perf_counter() - frame_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        cap.release()
        self.stop_event.set()
        # Reset tracker khi dừng
        self.lp_tracker.reset()


    def thread_read_camera(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, FPS_CAMERA)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])

        # Kiểm tra FPS thực của camera
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        resolution_name = get_resolution_name(actual_height)
        self.window.setDoPhanGiai(f"{resolution_name} ({actual_fps:.2f} FPS)")
        
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("[Thread Camera] Mất kết nối Camera.")
                self.stopAll()
                break

            # Convert BGR to RGB cho display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Giữ frame BGR gốc cho model (GPU sẽ xử lý BGR->RGB)
            frame_bgr = frame

            # Vứt bỏ frame cũ nếu queue đầy
            if not self.frame_queue.empty():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass

            # Nhét frame BGR và RGB vào queue (tuple: (bgr, rgb_for_display))
            self.frame_queue.put((frame_bgr, frame_rgb))

        cap.release()
        self.stop_event.set()

    def thread_process_ai(self):
        frame_count = 0
        is_new_plate = True
        frame_stopping = 0
        while not self.stop_event.is_set():
            try:
                frame_data = self.frame_queue.get(timeout=1)
            except queue.Empty:
                continue

            frame_count += 1

            if frame_count % 50 == 0 and torch.cuda.is_available(): #xóa cache CUDA mỗi 100 frame
                torch.cuda.empty_cache()
                print(f"[{frame_count}] CUDA cache cleared")

            # Lấy frame BGR cho model và RGB cho display
            if isinstance(frame_data, tuple):
                frame_bgr, frame_rgb = frame_data
            else:
                # Fallback: nếu queue chứa frame cũ (RGB)
                frame_rgb = frame_data
                frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGB2BGR)

            frame_h, frame_w, frame_ch = frame_rgb.shape
            bytes_per_line = frame_ch * frame_w
            
            t0 = time.perf_counter() # Bắt đầu đo thời gian dự đoán
            # Predict với BGR frame (GPU sẽ xử lý BGR->RGB và resize)
            license_plate, conf, detection = predict_license_plate(self.model, frame_bgr, size=IMG_SIZE_MODEL)
            t1 = time.perf_counter() # Kết thúc đo thời gian dự đoán

            # Parse detection và scale bbox
            bbox, conf_det = detection if detection else (None, 0.0)
            scaled_bbox = None
            if bbox is not None:
                bbox_x, bbox_y, bbox_w, bbox_h = bbox
                scale_x = frame_w / IMG_SIZE_MODEL[0]
                scale_y = frame_h / IMG_SIZE_MODEL[1]
                scaled_bbox = (
                    int(bbox_x * scale_x),
                    int(bbox_y * scale_y),
                    int(bbox_w * scale_x),
                    int(bbox_h * scale_y)
                )

            # Update tracker
            tracked_bbox, tracking_status = self.lp_tracker.update(
                    scaled_bbox, conf_det, conf 
                )
            t2 = time.perf_counter() # Kết thúc đo thời gian xử lý kết quả

            # Hiển thị frame với bbox tracking
            if tracked_bbox is not None:
                frame_display = frame_rgb.copy()
                bbox_x, bbox_y, bbox_w, bbox_h = tracked_bbox
                
                # Màu và text theo trạng thái
                if tracking_status == "DETECTED":
                    color = (0, 255, 0)  # Xanh lá: detection mới
                    thickness = 2
                    text = f"NEW {conf*100:.1f}% ({conf_det*100:.1f}%)"
                    self.history.clear()  # Xóa lịch sử cũ khi có biển số mới
                    is_new_plate = True
                elif tracking_status == "TRACKING" or tracking_status == "STOPPING":  # TRACKING
                    color = (255, 255, 0)  # Vàng: đang tracking
                    thickness = 3
                    text = f"TRACKING: {conf*100:.1f}% ({conf_det*100:.1f}%)"
                    # Lưu vào history
                    q_img_temp = QImage(frame_rgb.data, frame_w, frame_h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(q_img_temp).scaled(
                            self.window.imgBienSo.width(),
                            self.window.imgBienSo.height(),
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation,
                        )
                    self.history.append(Result(pixmap, license_plate, conf, time.time()))

                    if tracking_status == "STOPPING":
                        frame_stopping += 1
                        if frame_stopping > MAX_FRAME_STOPPING and is_new_plate == True:
                            best = max(self.history, key=lambda x: x.confidence)
                            if best.license_plate != self.previousLP.license_plate:
                                self.previousLP = best
                                self.displayResult(best.pixmap, best.license_plate, best.confidence)
                                is_new_plate = False
                    else:
                        frame_stopping = 0
                else: # LOST     
                    self.history.clear()
                    is_new_plate = True
                    frame_stopping = 0

                    
                # Vẽ rectangle (màu xanh lá)
                cv2.rectangle(frame_display, (bbox_x, bbox_y), (bbox_x + bbox_w, bbox_y + bbox_h), color, thickness)
                
                # Vẽ text (background box cho dễ đọc)
                (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame_display, (bbox_x, bbox_y - text_h - 10), (bbox_x + text_w, bbox_y), color, -1)
                cv2.putText(frame_display, text, (bbox_x, bbox_y - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                
                # Convert sang QImage
                q_img = QImage(frame_display.data,  frame_w, frame_h,  bytes_per_line,  QImage.Format_RGB888)
            else:
                print("LOST: "+is_new_plate.__str__()+" - "+len(self.history).__str__() )
                if is_new_plate == True and len(self.history) > 0: # Chưa trả kết quả cho biển số cũ
                    best = max(self.history, key=lambda x: x.confidence)
                    if best.license_plate != self.previousLP.license_plate:
                        self.previousLP = best
                        self.displayResult(best.pixmap, best.license_plate, best.confidence)
                    self.history.clear()
                
                # Không có bbox → hiển thị frame gốc
                q_img = QImage(frame_rgb.data, frame_w, frame_h, bytes_per_line, QImage.Format_RGB888)
            
            # # Scale và emit signal
            pixmap = QPixmap.fromImage(q_img).scaled(
                self.window.lblScreen.width(),
                self.window.lblScreen.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )    

            self.signals.update_frame.emit(pixmap)  # Emit signal thay vì gọi trực tiếp
            t3 = time.perf_counter() # Kết thúc đo thời gian hiển thị

            # In thời gian chi tiết
            time_model = (t1 - t0) * 1000
            time_post = (t2 - t1) * 1000
            time_display = (t3 - t2) * 1000
            time_total = (t3 - t0) * 1000
            # print(f"Model: {time_model:.1f}ms | Post: {time_post:.1f}ms | Display: {time_display:.1f}ms | Total: {time_total:.1f}ms")

            if frame_count > 20:
                self.minInferenceTime = min(self.minInferenceTime, time_model) if self.minInferenceTime > 0 else time_model
                self.maxInferenceTime = max(self.maxInferenceTime, time_model)
                self.minSystemTime = min(self.minSystemTime, time_total) if self.minSystemTime > 0 else time_total
                self.maxSystemTime = max(self.maxSystemTime, time_total)

            # Tính FPS
            if time_total > 0:
                instant_fps = 1000.0 / time_total
                if frame_count > 20:
                    self.minFPS = min(self.minFPS, instant_fps) if self.minFPS > 0 else instant_fps
                    self.maxFPS = max(self.maxFPS, instant_fps)

            # print("Min system: ", f"{self.minSystemTime:.2f}", "Max system: ", f"{self.maxSystemTime:.2f}", "Min inference: ", f"{self.minInferenceTime:.2f}", "Max inference: ", f"{self.maxInferenceTime:.2f}", "Min FPS: ", f"{self.minFPS:.0f}", "Max FPS: ", f"{self.maxFPS:.0f}")
            
            self.signals.update_fps.emit(time_model, time_total, instant_fps)  # Emit signal thay vì gọi trực tiếp

        print("[Thread AI] Stopped.")

    # Slot methods - chạy trên main thread
    def _update_frame_ui(self, pixmap):
        self.window.lblScreen.setPixmap(pixmap)

    def _update_fps_ui(self, timeModel, timeSystem, fps):
        self.window.setTimeModel(timeModel)
        self.window.setTimeSystem(timeSystem)
        self.window.setFPS(fps)

    def _update_result_ui(self, pixmap, license_plate, conf):
        self.window.setLabelBienSo(f"{license_plate}")
        self.window.setLabelTime(f"{(conf * 100):.2f}%")
        self.window.setImgKq(pixmap)

    def displayResult(self, pixmap, license_plate, conf):
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        self.window.addItemListView(f"{license_plate} - {(conf * 100):.2f}% - {current_time}")
        # Emit signal thay vì cập nhật UI trực tiếp
        self.signals.update_result.emit(pixmap, license_plate, conf)

    def start(self):
        self.window.setEventButtonCamera(self.handleOpenCamera)
        self.window.setEventButtonVideo(self.handleVideo)
        self.window.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    system = System('Model_YOLO_RVT\\final_yolo_rvit_model_E2E_92.pth')
    system.start()
    sys.exit(app.exec_())   