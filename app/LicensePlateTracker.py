from collections import deque

class LicensePlateTracker:
    """
    Tracker với combined confidence:
    - Dùng (conf_det + conf_ocr) / 2 để quyết định có update không
    - Đợi 1-2 frame khi confidence thấp trước khi mất tracking
    """
    def __init__(self, iou_threshold=0.1, max_missing_frames=15, smoothing_window=5, conf_threshold=0.6):
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames  # Đợi 15 frames trước khi reset
        self.smoothing_window = smoothing_window
        self.conf_threshold = conf_threshold  # Combined conf threshold
        
        # Tracking state
        self.last_bbox = None
        self.bbox_history = deque(maxlen=smoothing_window)
        self.missing_frames = 0
        self.is_tracking = False

        #State stopping
        self.frame_lost = 0
        
    def calculate_iou(self, bbox1, bbox2):
        """Tính IoU giữa 2 bbox (x, y, w, h)"""
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        x1_br, y1_br = x1 + w1, y1 + h1
        x2_br, y2_br = x2 + w2, y2 + h2
        
        inter_x1 = max(x1, x2)
        inter_y1 = max(y1, y2)
        inter_x2 = min(x1_br, x2_br)
        inter_y2 = min(y1_br, y2_br)
        
        if inter_x2 < inter_x1 or inter_y2 < inter_y1:
            return 0.0
        
        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area
        
        return inter_area / union_area if union_area > 0 else 0.0
    
    def update(self, detected_bbox, conf_det, conf_ocr):
        if detected_bbox is not None:
            if conf_ocr >= 0.7:
                if self.is_tracking and self.last_bbox is not None: #đang tracking
                    iou = self.calculate_iou(detected_bbox, self.last_bbox)
        
                    if iou > self.iou_threshold: #cùng biển số trước đó
                        self.last_bbox = detected_bbox
                        self.missing_frames = 0
                        if iou > 0.8:
                            return self.last_bbox, "STOPPING"
                        
                        self.frame_lost = 0
                        return self.last_bbox, "TRACKING"
                    else: #biển số mới
                        self.last_bbox = detected_bbox
                        self.missing_frames = 0
                        self.is_tracking = True
                        self.frame_lost += 1
                        if self.frame_lost > 2:
                            self.frame_lost = 0
                            return detected_bbox, "DETECTED"
                        return detected_bbox, "TRACKING"
                           
                else: #chưa tracking
                    self.last_bbox = detected_bbox
                    self.missing_frames = 0
                    self.is_tracking = True
                    return detected_bbox, "DETECTED"
            else: #không đạt threshold
                if conf_ocr < 0.6:
                    self.reset()
                    return None, "LOST"
                
                if self.is_tracking and self.last_bbox is not None:
                    self.missing_frames += 1
                    if self.missing_frames <= self.max_missing_frames:
                        return self.last_bbox, "TRACKING"
                    else:
                        self.reset()
                        return None, "LOST"
                return None, "LOST"
        else: #detected_bbox is None
            if conf_ocr > 0.7:
                self.missing_frames += 1
                if self.missing_frames <= self.max_missing_frames:
                    return self.last_bbox, "TRACKING"
                else:
                    self.reset()
                    return None, "LOST"
            
            self.reset()
            return None, "LOST"
    
    def reset(self):
        """Reset tracker - xe đã ra khỏi frame"""
        self.last_bbox = None
        self.bbox_history.clear()
        self.missing_frames = 0
        self.is_tracking = False