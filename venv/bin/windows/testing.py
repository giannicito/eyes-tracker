from imutils import face_utils
import imutils
import cv2
import pyautogui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QPushButton
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap, QImage, QTransform, QColor, QPainter
import classes.processes as processes
import os

class TestingWindow(QWidget):
    def __init__(self, parent=None):
        super(TestingWindow, self).__init__(parent)

        # initialize variables
        self.width = parent.width
        self.height = parent.height

        print("w: " + str(self.width))
        print("h: " + str(self.height))

        self.leftTop = QLabel("Left Top Corner", self)
        self.leftTop.setGeometry(0, 0, int(self.width / 2), int(self.height / 2))
        self.leftTop.setAlignment(Qt.AlignCenter)
        self.leftTop.setStyleSheet("QLabel { background-color: rgba(255, 0, 0, 30); }")

        self.leftBottom = QLabel("Left Bottom Corner", self)
        self.leftBottom.setGeometry(0, int(self.height / 2), int(self.width / 2), int(self.height / 2))
        self.leftBottom.setAlignment(Qt.AlignCenter)
        self.leftBottom.setStyleSheet("QLabel { background-color: rgb(0, 255, 0, 30); }")

        self.rightTop = QLabel("Right Top Corner", self)
        self.rightTop.setGeometry(int(self.width / 2), 0, int(self.width / 2), int(self.height / 2))
        self.rightTop.setAlignment(Qt.AlignCenter)
        self.rightTop.setStyleSheet("QLabel { background-color: rgba(0, 0, 255, 30); }")

        self.rightBottom = QLabel("Right Bottom Corner", self)
        self.rightBottom.setGeometry(int(self.width / 2), int(self.height / 2), int(self.width / 2), int(self.height / 2))
        self.rightBottom.setAlignment(Qt.AlignCenter)
        self.rightBottom.setStyleSheet("QLabel { background-color: rgba(0, 0, 0, 30); }")

        self.point_pos = []
        self.left_limit = 0
        self.right_limit = 0
        self.top_limit = 0
        self.bottom_limit = 0
        self.middleh_limit = 0
        self.middlev_limit = 0
        self.contrastThreshold = 70
        self.getCalibrationData()

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(0)

        self.circle = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../image", "circle.png"))

    def getArrowPixmap(self, p, identifier, position, color=QColor(255, 0, 0, 255)):
        self.targetPoint.move(position[0], position[1])
        pixmap = p.copy()

        mask = pixmap.createMaskFromColor(QColor(0, 0, 0), Qt.MaskOutColor)

        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setPen(color)
        p.drawPixmap(pixmap.rect(), mask, mask.rect())
        p.end()
        self.display_image(None, identifier, pixmap)

    def update_frame(self):
        _, frame = self.capture.read()
        frame = cv2.flip(frame, 1)
        frame = imutils.resize(frame, width=640)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_detected = self.detector(gray)

        if len(faces_detected) > 0:
            face = faces_detected[0]

            # faces points found by dlib library
            landmarks = self.predict(gray, face)

            # Detect blinking
            left_eye_ratio = processes.get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
            right_eye_ratio = processes.get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)
            blinking_ratio = (left_eye_ratio + right_eye_ratio) / 2


            # detect eye direction
            le_direction, le_bw, le_n = processes.detect_eye_direction(frame, gray, [36, 37, 38, 39, 40, 41], landmarks, self.contrastThreshold)
            re_direction, re_bw, re_n = processes.detect_eye_direction(frame, gray, [42, 43, 44, 45, 46, 47], landmarks, self.contrastThreshold)

            hor_dir = (le_direction + re_direction) / 2
            ver_dir = processes.getEyeTopPosition([37, 38, 41, 40], landmarks)

            screen_side = 0
            if hor_dir >= self.left_limit and hor_dir <= self.middlev_limit and ver_dir <= self.top_limit and ver_dir >= self.middleh_limit:
                self.setActiveSide(0)
            elif hor_dir >= self.left_limit and hor_dir <= self.middlev_limit and ver_dir <= self.middleh_limit and ver_dir >= self.bottom_limit:
                self.setActiveSide(1)
            elif hor_dir >= self.middlev_limit and hor_dir <= self.right_limit and ver_dir <= self.top_limit and ver_dir >= self.middleh_limit:
                self.setActiveSide(2)
            elif hor_dir >= self.middlev_limit and hor_dir <= self.right_limit and ver_dir <= self.middleh_limit and ver_dir >= self.bottom_limit:
                self.setActiveSide(3)

        #self.display_image(frame, "face")


    def setActiveSide(self, number):
        if number == 0:
            # top left
            self.leftTop.setStyleSheet("QLabel { background-color: rgba(255, 0, 0, 255); }")
        else:
            self.leftTop.setStyleSheet("QLabel { background-color: rgba(255, 0, 0, 30); }")

        if number == 1:
            # bottom left
            self.leftBottom.setStyleSheet("QLabel { background-color: rgb(0, 255, 0, 255); }")
        else:
            self.leftBottom.setStyleSheet("QLabel { background-color: rgb(0, 255, 0, 30); }")

        if number == 2:
            # top right
            self.rightTop.setStyleSheet("QLabel { background-color: rgba(0, 0, 255, 255); }")
        else:
            self.rightTop.setStyleSheet("QLabel { background-color: rgba(0, 0, 255, 30); }")

        if number == 3:
            # bottom right
            self.rightBottom.setStyleSheet("QLabel { background-color: rgba(0, 0, 0, 255); }")
        else:
            self.rightBottom.setStyleSheet("QLabel { background-color: rgba(0, 0, 0, 30); }")


    def getCalibrationData(self):
        f = open("./conf/calibration.dat", "r")

        for line in f:
            arr = line.split(",")
            self.left_limit = float(arr[0])
            self.right_limit = float(arr[1])
            self.top_limit = float(arr[2])
            self.bottom_limit = float(arr[3])
            self.middleh_limit = float(arr[4])
            self.middlev_limit = float(arr[5])
            self.contrastThreshold = int(arr[6])

        print(self.left_limit)
        print(self.right_limit)
        print(self.top_limit)
        print(self.bottom_limit)
        print(self.middleh_limit)
        print(self.middlev_limit)

        f.close()


    def display_image(self, img, window, pixmap=None):
        if img is not None:
            # Makes OpenCV images displayable on PyQT, displays them
            qformat = QImage.Format_Indexed8
            if len(img.shape) == 3:
                if img.shape[2] == 4:  # RGBA
                    qformat = QImage.Format_RGBA8888
                else:  # RGB
                    qformat = QImage.Format_RGB888

            out_image = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)  # BGR to RGB
            out_image = out_image.rgbSwapped()

            if window == 'face':  # main window
                self.baseImage.setPixmap(QPixmap.fromImage(out_image))
                self.baseImage.setScaledContents(True)
            if window == 'left-eye':  # left eye window
                self.leftEye.setPixmap(QPixmap.fromImage(out_image))
                self.leftEye.setScaledContents(True)
            if window == 'left-eye-contrast':  # left eye contrast
                self.leftEyeBW.setPixmap(QPixmap.fromImage(out_image))
                self.leftEyeBW.setScaledContents(True)
            if window == 'right-eye':  # right eye window
                self.rightEye.setPixmap(QPixmap.fromImage(out_image))
                self.rightEye.setScaledContents(True)
            if window == 'right-eye-contrast':  # right eye window
                self.rightEyeBW.setPixmap(QPixmap.fromImage(out_image))
                self.rightEyeBW.setScaledContents(True)
        else:
            if window == 'top-arrow':
                self.topArrow.setPixmap(pixmap)
                self.topArrow.setScaledContents(True)
            if window == 'down-arrow':
                self.downArrow.setPixmap(pixmap)
                self.downArrow.setScaledContents(True)
            if window == 'left-arrow':
                self.leftArrow.setPixmap(pixmap)
                self.leftArrow.setScaledContents(True)
            if window == 'right-arrow':
                self.rightArrow.setPixmap(pixmap)
                self.rightArrow.setScaledContents(True)
            if window == 'center-circle':
                self.centerCircle.setPixmap(pixmap)
                self.centerCircle.setScaledContents(True)
            if window == 'goal-point':
                self.targetPoint.setPixmap(pixmap)
                self.targetPoint.setScaledContents(True)


