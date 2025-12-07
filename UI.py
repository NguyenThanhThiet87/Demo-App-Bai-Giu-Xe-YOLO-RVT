from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage, QStandardItemModel, QStandardItem

class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('untitled.ui', self)

          # Tạo model cho ListView
        self.listModel = QStandardItemModel()
        self.listView.setModel(self.listModel)

    def setFPS(self, fps):
        self.lblFPS.setText(f"FPS: {fps:.0f}")
    def setDoPhanGiai(self, do_phan_giai):
        self.lblResolution.setText(f"Resolution: {do_phan_giai}")
    def setTimeModel(self, time_model):
        self.lblFPS_Model.setText(f"Time Model: {time_model:.2f} ms")
    def setTimeSystem(self, time_system):
        self.lblFPS_System.setText(f"Time System: {time_system:.2f} ms")

    def setImgKq(self, img):
        self.imgBienSo.setPixmap(img)
    
    def setLabelBienSo(self, text):
        self.lblKQBienSo.setText(text)
    
    def setLabelTime(self, text):
        self.lblTime.setText(text)

    def setEventButtonCamera(self, func):
        self.btnCamera.clicked.connect(func)

    def setEventButtonVideo(self, func):
        self.btnVideo.clicked.connect(func)

    def addItemListView(self, text):
        item = QStandardItem(text)
        self.listModel.insertRow(0, item)

    def start(self):
        self.show()