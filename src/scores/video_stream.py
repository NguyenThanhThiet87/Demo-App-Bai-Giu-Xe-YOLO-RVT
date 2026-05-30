import cv2
import time
import queue

FRAME_SIZE = (1280, 1080)
FPS_CAMERA = 60

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
        
def thread_read_video(video_path, frame_queue, stop_event, window_ui, lp_tracker):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[Thread Video] Cannot open video: {video_path}")
        stop_event.set()
        return
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # Lấy độ phân giải gốc của video
    video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    resolution_name = get_resolution_name(video_height)
    window_ui.setDoPhanGiai(f"{resolution_name} ({video_fps:.2f} FPS)")
    # Giới hạn FPS (giống camera)
    target_fps = min(video_fps, FPS_CAMERA)
    frame_delay = 1.0 / target_fps
    
    print(f"[Thread Video] Video: {total_frames} frames, {video_fps:.2f} FPS (limited to {target_fps:.0f} FPS)")
    while not stop_event.is_set():
        frame_start = time.perf_counter()
        
        ret, frame = cap.read()
        if not ret:
            break
        # Convert sang RGB cho display (bỏ qua CPU resize dư thừa để luồng GUI chính tự scale bằng phần cứng)
        frame_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Giữ frame gốc BGR cho model (GPU sẽ xử lý resize và BGR->RGB)
        frame_bgr = frame
        # Vứt bỏ frame cũ nếu queue đầy để luôn xử lý frame mới nhất (Cách 1: Real-time giống camera)
        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        
        # Nhét frame BGR và RGB vào queue (tuple: (bgr, rgb_for_display))
        frame_queue.put((frame_bgr, frame_display))
        
        # Giới hạn tốc độ đọc frame mô phỏng FPS thực tế của Video thời gian thực (Cách 1)
        elapsed = time.perf_counter() - frame_start
        sleep_time = frame_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
    cap.release()
    stop_event.set()
    # Reset tracker khi dừng
    lp_tracker.reset()

def thread_read_camera(camera_index, frame_queue, stop_event, window_ui, system_instance):
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FPS, FPS_CAMERA)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_SIZE[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_SIZE[1])
    # Kiểm tra FPS thực của camera
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    resolution_name = get_resolution_name(actual_height)
    window_ui.setDoPhanGiai(f"{resolution_name} ({actual_fps:.2f} FPS)")
    
    while not stop_event.is_set():
        ret, frame = cap.read()
        if not ret:
            print("[Thread Camera] Mất kết nối Camera.")
            system_instance.stopAll()
            break
        # Convert BGR to RGB cho display
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Giữ frame BGR gốc cho model (GPU sẽ xử lý BGR->RGB)
        frame_bgr = frame
        # Vứt bỏ frame cũ nếu queue đầy
        if not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
        # Nhét frame BGR và RGB vào queue (tuple: (bgr, rgb_for_display))
        frame_queue.put((frame_bgr, frame_rgb))
    cap.release()
    stop_event.set()