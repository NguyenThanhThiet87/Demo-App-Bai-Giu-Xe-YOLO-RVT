from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage

class SignalEmitter(QObject):
    """Signal emitter để cập nhật UI an toàn từ thread khác"""
    update_frame = Signal(QImage)  # Signal để cập nhật frame
    update_fps = Signal(float, float, float)       # Signal để cập nhật FPS
    update_result = Signal(QImage, str, float)  # Signal để cập nhật kết quả
