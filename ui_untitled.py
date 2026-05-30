# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'untitled.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QListView, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1053, 637)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setStyleSheet(u"background-color: gray;")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(20, 20, 20, 20)
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setStyleSheet(u"background-color: #ffffff; border-radius: 10px;")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame_3 = QFrame(self.frame)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_3)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.lblResolution = QLabel(self.frame_3)
        self.lblResolution.setObjectName(u"lblResolution")

        self.horizontalLayout_3.addWidget(self.lblResolution)

        self.lblFPS_Model = QLabel(self.frame_3)
        self.lblFPS_Model.setObjectName(u"lblFPS_Model")

        self.horizontalLayout_3.addWidget(self.lblFPS_Model)

        self.lblFPS_System = QLabel(self.frame_3)
        self.lblFPS_System.setObjectName(u"lblFPS_System")

        self.horizontalLayout_3.addWidget(self.lblFPS_System)

        self.lblFPS = QLabel(self.frame_3)
        self.lblFPS.setObjectName(u"lblFPS")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.lblFPS.setFont(font)
        self.lblFPS.setLayoutDirection(Qt.LeftToRight)
        self.lblFPS.setStyleSheet(u"padding-right:10px")
        self.lblFPS.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_3.addWidget(self.lblFPS)


        self.verticalLayout_2.addWidget(self.frame_3)

        self.lblScreen = QLabel(self.frame)
        self.lblScreen.setObjectName(u"lblScreen")
        self.lblScreen.setStyleSheet(u"background-color:black; color: white;")
        self.lblScreen.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.lblScreen)

        self.frame_2 = QFrame(self.frame)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy1)
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setSpacing(50)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(50, 0, 50, 0)
        self.btnCamera = QPushButton(self.frame_2)
        self.btnCamera.setObjectName(u"btnCamera")
        self.btnCamera.setStyleSheet(u"background-color: red; color: white;padding: 5px")

        self.horizontalLayout_2.addWidget(self.btnCamera)

        self.btnVideo = QPushButton(self.frame_2)
        self.btnVideo.setObjectName(u"btnVideo")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.btnVideo.sizePolicy().hasHeightForWidth())
        self.btnVideo.setSizePolicy(sizePolicy2)
        self.btnVideo.setStyleSheet(u"background-color: blue; color: white;padding: 5px;")

        self.horizontalLayout_2.addWidget(self.btnVideo)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout_2.addWidget(self.frame_2)

        self.verticalLayout_2.setStretch(1, 9)
        self.verticalLayout_2.setStretch(2, 1)

        self.horizontalLayout.addWidget(self.frame)

        self.frame_5 = QFrame(self.centralwidget)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.StyledPanel)
        self.frame_5.setFrameShadow(QFrame.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_5)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame_6 = QFrame(self.frame_5)
        self.frame_6.setObjectName(u"frame_6")
        self.frame_6.setStyleSheet(u"background-color: #ffffff; border-radius: 10px;")
        self.frame_6.setFrameShape(QFrame.StyledPanel)
        self.frame_6.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_6)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(10, -1, 10, -1)
        self.lblKq = QLabel(self.frame_6)
        self.lblKq.setObjectName(u"lblKq")
        font1 = QFont()
        font1.setPointSize(11)
        font1.setBold(True)
        self.lblKq.setFont(font1)

        self.verticalLayout_3.addWidget(self.lblKq)

        self.imgBienSo = QLabel(self.frame_6)
        self.imgBienSo.setObjectName(u"imgBienSo")
        self.imgBienSo.setAutoFillBackground(False)
        self.imgBienSo.setStyleSheet(u"background-color: gray;")
        self.imgBienSo.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.imgBienSo)

        self.lblKQBienSo = QLabel(self.frame_6)
        self.lblKQBienSo.setObjectName(u"lblKQBienSo")
        font2 = QFont()
        font2.setPointSize(15)
        font2.setBold(True)
        self.lblKQBienSo.setFont(font2)
        self.lblKQBienSo.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lblKQBienSo)

        self.lblTime = QLabel(self.frame_6)
        self.lblTime.setObjectName(u"lblTime")
        font3 = QFont()
        font3.setPointSize(7)
        self.lblTime.setFont(font3)
        self.lblTime.setStyleSheet(u"color: gray;")
        self.lblTime.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.lblTime)

        self.verticalLayout_3.setStretch(1, 6)
        self.verticalLayout_3.setStretch(2, 2)

        self.verticalLayout.addWidget(self.frame_6)

        self.frame_7 = QFrame(self.frame_5)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setStyleSheet(u"background-color: #ffffff; border-radius: 10px;")
        self.frame_7.setFrameShape(QFrame.StyledPanel)
        self.frame_7.setFrameShadow(QFrame.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame_7)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.lblNhatKy_2 = QLabel(self.frame_7)
        self.lblNhatKy_2.setObjectName(u"lblNhatKy_2")
        self.lblNhatKy_2.setFont(font1)

        self.verticalLayout_4.addWidget(self.lblNhatKy_2)

        self.listView = QListView(self.frame_7)
        self.listView.setObjectName(u"listView")

        self.verticalLayout_4.addWidget(self.listView)

        self.verticalLayout_4.setStretch(1, 9)

        self.verticalLayout.addWidget(self.frame_7)

        self.verticalLayout.setStretch(0, 5)
        self.verticalLayout.setStretch(1, 5)

        self.horizontalLayout.addWidget(self.frame_5)

        self.horizontalLayout.setStretch(0, 7)
        self.horizontalLayout.setStretch(1, 3)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1053, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.lblResolution.setText(QCoreApplication.translate("MainWindow", u"Resolution: 1080p (30fps)", None))
        self.lblFPS_Model.setText(QCoreApplication.translate("MainWindow", u"Time Model: 10ms", None))
        self.lblFPS_System.setText(QCoreApplication.translate("MainWindow", u"Time System: 20ms ", None))
        self.lblFPS.setText(QCoreApplication.translate("MainWindow", u"FPS 30", None))
        self.lblScreen.setText(QCoreApplication.translate("MainWindow", u"Screen", None))
        self.btnCamera.setText(QCoreApplication.translate("MainWindow", u"Open Camera", None))
        self.btnVideo.setText(QCoreApplication.translate("MainWindow", u"Choose Video", None))
        self.lblKq.setText(QCoreApplication.translate("MainWindow", u"K\u1ebft qu\u1ea3 hi\u1ec7n t\u1ea1i", None))
        self.imgBienSo.setText(QCoreApplication.translate("MainWindow", u"imgBienSo", None))
        self.lblKQBienSo.setText(QCoreApplication.translate("MainWindow", u"59E190375", None))
        self.lblTime.setText(QCoreApplication.translate("MainWindow", u"\u0110\u1ed9 ch\u00ednh x\u00e1c", None))
        self.lblNhatKy_2.setText(QCoreApplication.translate("MainWindow", u"Nh\u1eadt k\u00fd", None))
    # retranslateUi

