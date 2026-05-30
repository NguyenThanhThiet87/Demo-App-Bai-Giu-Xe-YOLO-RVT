import threading
import queue
import time
import cv2
from collections import deque
from datetime import datetime
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage

from src.schemas.Result import Result
from src.schemas.SignalEmiiter import SignalEmitter
from UI import UI
from src.AI.predict import predict_license_plate, load_model
from LicensePlateTracker import LicensePlateTracker
from src.scores.video_stream import thread_read_video, thread_read_camera
from database import MongoDB
from src.schemas.ParkingRecord import ParkingRecord

MAX_FRAME_STOPPING = 15
IMG_SIZE_MODEL = (640, 640)

class System:
    def __init__(self, path_model):
        if path_model.endswith('.engine'):
            self.model = load_model(path_model)
            print(f"Using Model: {path_model}")
        elif path_model.endswith('.onnx'):
            self.model = load_model(path_model)
            print(f"Using Model: {path_model}")
        else:
            raise FileNotFoundError(f"Model file not found: {path_model}")
        
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

        # Queue và Thread chuyên dụng cho MongoDB chạy nền hoàn toàn độc lập
        self.mongo_queue = queue.Queue()
        self.mongo_thread = threading.Thread(target=self._mongo_worker, daemon=True)
        self.mongo_thread.start()

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
        # Tạo và chạy threads truyền argument
        self.thread_read = threading.Thread(target=thread_read_video, args=(self.video_path, self.frame_queue, self.stop_event, self.window, self.lp_tracker), daemon=True)
        self.thread_ai = threading.Thread(target=self.thread_process_ai, daemon=True)
        self.thread_read.start()
        self.thread_ai.start()

    def handleOpenCamera(self):
        self.stopAll()

        self.stop_event.clear()
        # Tạo và chạy threads truyền argument
        self.thread_read = threading.Thread(target=thread_read_camera, args=(0, self.frame_queue, self.stop_event, self.window, self), daemon=True)
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

            # Predict với BGR frame
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
                    # Lưu vào history (sử dụng QImage.copy() để cô lập vùng nhớ an toàn đa luồng)
                    q_img_temp = QImage(frame_rgb.data, frame_w, frame_h, bytes_per_line, QImage.Format_RGB888).copy()
                    self.history.append(Result(q_img_temp, license_plate, conf, time.time()))

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

            # Emit QImage trực tiếp để luồng GUI chính xử lý hiển thị
            self.signals.update_frame.emit(q_img.copy())
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
                if frame_count > 100:
                    self.minFPS = min(self.minFPS, instant_fps) if self.minFPS > 0 else instant_fps
                    self.maxFPS = max(self.maxFPS, instant_fps)

            print("Min system: ", f"{self.minSystemTime:.2f}", "Max system: ", f"{self.maxSystemTime:.2f}", "Min inference: ", f"{self.minInferenceTime:.2f}", "Max inference: ", f"{self.maxInferenceTime:.2f}", "Min FPS: ", f"{self.minFPS:.0f}", "Max FPS: ", f"{self.maxFPS:.0f}")

            self.signals.update_fps.emit(time_model, time_total, instant_fps)  # Emit signal thay vì gọi trực tiếp

        # Khi thread kết thúc, in báo cáo
        print("[Thread AI] Stopped.")

        # Slot methods - chạy trên main thread
    def _update_frame_ui(self, q_img):
        # Thực hiện việc tạo QPixmap và scaled trên luồng GUI chính (main thread) để đạt FPS tối đa và an toàn luồng
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.window.lblScreen.width(),
            self.window.lblScreen.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.window.lblScreen.setPixmap(pixmap)

    def _update_fps_ui(self, timeModel, timeSystem, fps):
        self.window.setTimeModel(timeModel)
        self.window.setTimeSystem(timeSystem)
        self.window.setFPS(fps)

    def _update_result_ui(self, q_img, license_plate, conf):
        # 1. Thêm kết quả vào ListView một cách an toàn trên luồng chính
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        self.window.addItemListView(f"{license_plate} - {(conf * 100):.2f}% - {current_time}")

        # 2. Tạo QPixmap từ QImage và scale hiển thị ảnh kết quả
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.window.imgBienSo.width(),
            self.window.imgBienSo.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.window.setLabelBienSo(f"{license_plate}")
        self.window.setLabelTime(f"{(conf * 100):.2f}%")
        self.window.setImgKq(pixmap)

    def displayResult(self, q_img, license_plate, conf):
        # Chỉ emit signal, để luồng chính xử lý cập nhật giao diện
        self.signals.update_result.emit(q_img, license_plate, conf)

        # Đẩy vào queue nền để MongoDB worker xử lý bất đồng bộ, tuyệt đối không block luồng xử lý AI/GUI
        self.mongo_queue.put((q_img, license_plate, conf))

    def _mongo_worker(self):
        """Luồng chạy nền xử lý lưu trữ MongoDB độc lập hoàn toàn với AI và GUI"""
        print("[MongoDB Worker] Luồng lưu DB nền đã khởi động.")
        # Kết nối DB một lần duy nhất lúc khởi động luồng
        db = MongoDB.get_db()
        
        while not self.stop_event.is_set():
            try:
                # Đợi có bản ghi cần lưu trong tối đa 1 giây
                task = self.mongo_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            q_img, license_plate, conf = task
            try:
                if db is None:
                    db = MongoDB.get_db()
                    
                if db is not None:
                    record = ParkingRecord(license_plate, conf, q_img)
                    db["parking_records"].insert_one(record.to_dict())
                    print(f"[DB] Đã lưu biển số {license_plate} vào MongoDB thành công.")
            except Exception as e:
                print(f"[DB] Lỗi khi lưu MongoDB: {e}")
            finally:
                self.mongo_queue.task_done()

    def start(self):
        self.window.setEventButtonCamera(self.handleOpenCamera)
        self.window.setEventButtonVideo(self.handleVideo)
        self.window.start()