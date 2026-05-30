from datetime import datetime
import base64
from PySide6.QtCore import QByteArray, QBuffer, QIODevice

class ParkingRecord:
    def __init__(self, license_plate: str, confidence: float, pixmap=None, camera_id: str = "CAM_01"):
        self.license_plate = license_plate
        self.confidence = float(confidence)
        self.timestamp = datetime.now()
        self.camera_id = camera_id
        
        # Chuyển đổi QPixmap (ảnh) sang chuỗi Base64 để lưu vào MongoDB
        self.image_base64 = None
        if pixmap is not None:
            self.image_base64 = self._pixmap_to_base64(pixmap)

    def _pixmap_to_base64(self, pixmap) -> str:
        """Chuyển đổi QPixmap thành chuỗi Base64 định dạng JPEG."""
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        # Lưu ảnh dưới dạng JPEG chất lượng 80% để giảm dung lượng DB
        pixmap.save(buffer, "JPEG", 80)
        return byte_array.toBase64().data().decode("utf-8")

    def to_dict(self) -> dict:
        """Xuất ra dictionary chuẩn để insert vào MongoDB."""
        return {
            "license_plate": self.license_plate,
            "confidence": round(self.confidence, 4),
            "camera_id": self.camera_id,
            "timestamp": self.timestamp, # PyMongo tự động convert datetime sang kiểu Date của MongoDB
            "image_base64": self.image_base64
        }
