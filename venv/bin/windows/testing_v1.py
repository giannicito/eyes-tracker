from imutils import face_utils
import imutils
import cv2
import pyautogui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QPushButton
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter
import classes.processes as processes
import os
import numpy as np

class TestingWindow(QWidget):
    def __init__(self, parent=None):
        super(TestingWindow, self).__init__(parent)

        pyautogui.FAILSAFE = False

        # initialize variables
        self.width = parent.width
        self.height = parent.height

        self.tiles = []
        self.colors_tiles = [
            "255, 0, 0", "255, 127, 0", "255, 255, 0", "127, 255, 0",
            "0, 255, 127", "0, 255, 255", "0, 127, 255", "0, 0, 255",
            "127, 0, 255", "255, 0, 255", "255, 0, 127", "128, 128, 128"
        ]

        keyboard = [
            "DEL", #0
            "G H I", #1
            "P Q R S", #2
            "<---", #3
            "A B C", #4
            "J K L", #5
            "T U V", #6
            "_____", #7
            "D E F", #8
            "M N O", #9
            "W X Y Z", #10
            "--->" #11
        ]
        for i in range(3):
            for j in range(4):
                label = QLabel(keyboard[(j + (i * 4))], self)
                label.setGeometry((self.width / 3) * i, (self.height / 4) * j, int(self.width / 3), int(self.height / 4))
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet("QLabel { background-color: rgba(" + self.colors_tiles[j + (i * 3)] + ", 30); }")
                self.tiles.append(label)

        self.point_pos = []
        self.left_limit = 0
        self.right_limit = 0
        self.top_limit = 0
        self.bottom_limit = 0
        self.middleh_limit = 0
        self.middlev_limit = 0
        self.contrastThreshold = 70

        self.getCalibrationData()

        self.window_side = -1
        self.frame_pos = []

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.old_face = None
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

        r = 500.0 / frame.shape[1]
        dim = (500, int(frame.shape[0] * r))

        # perform the actual resizing of the image and show it
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_detected = self.detector(gray, 0)

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

            print(hor_dir)

            self.frame_pos.append([hor_dir, ver_dir])

            if blinking_ratio > 5.7:
                # probably blinking
                print("blinking")

            frame_check = 0

            if hor_dir > self.middlev_limit + (self.middlev_limit / 8):
                print("right")
            elif hor_dir < self.middlev_limit - (self.middlev_limit / 8):
                print("left")
            else:
                print("center")

            for i in range(3):
                for j in range(4):
                    left, right, top, bottom, x, y = self.getLimits(i, j)
                    if hor_dir >= left and hor_dir <= right and ver_dir <= top and ver_dir >= bottom:
                        if self.window_side == (i * 4) + j:
                            if len(self.frame_pos) >= frame_check:
                                h, v = self.getAverageXYPoint()
                                x, y = self.getScreenPosition(h, v, left, right, top, bottom, x, y)
                                self.setActiveSide((i * 4) + j, h, v)
                                self.frame_pos = []
                        else:
                            self.window_side = (i * 4) + j
                            self.frame_pos = [self.frame_pos[-1]]
            #x, y = self.getGlobalPosition(hor_dir, ver_dir, self.left_limit, self.right_limit, self.top_limit, self.bottom_limit)


        #self.display_image(frame, "face")

    def getLimits(self, col, row):
        if col == 0:
            x = 0
            left = self.left_limit
            right = self.middlev_limit - ((self.middlev_limit - self.left_limit) / 2)
        elif col == 1:
            x = int(self.width / 3)
            left = self.middlev_limit - ((self.middlev_limit - self.left_limit) / 2)
            right = self.middlev_limit + ((self.right_limit - self.middlev_limit) / 2)
        else:
            x = int((self.width * 2) / 3)
            left = self.middlev_limit + ((self.right_limit - self.middlev_limit) / 2)
            right = self.right_limit

        if row == 0:
            y = 0
            top = self.top_limit
            bottom = self.top_limit - ((self.top_limit - self.middleh_limit) / 2)
        elif row == 1:
            y = int(self.height / 4)
            top = self.top_limit - ((self.top_limit - self.middleh_limit) / 2)
            bottom = self.middleh_limit
        elif row == 2:
            y = int((self.height / 4) * 2)
            top = self.middleh_limit
            bottom = self.middleh_limit - ((self.middleh_limit - self.bottom_limit) / 2)
        else:
            y = int((self.height / 4) * 3)
            top = self.middleh_limit - ((self.middleh_limit - self.bottom_limit) / 2)
            bottom = self.bottom_limit

        return left, right, top, bottom, x, y


    def getAverageXYPoint(self):
        x = 0
        y = 0
        for i in range(len(self.frame_pos)):
            x += self.frame_pos[i][0]
            y += self.frame_pos[i][1]

        x /= len(self.frame_pos)
        y /= len(self.frame_pos)

        return x, y

    def getScreenPosition(self, h, v, left, right, top, bottom, x1, y1):
        x = int((h - left) * (self.width / 3) / (right - left)) + x1
        y = int((top - v) * (self.height / 4) / (top - bottom)) + y1
        pyautogui.moveTo(x, y)
        return x, y

    def getGlobalPosition(self, h, v, left, right, top, bottom):
        x = int((h - left) * self.width / (right - left))
        y = int((top - v) * self.height / (top - bottom))
        pyautogui.moveTo(x, y)
        return x, y

    def setActiveSide(self, number, x, y):
        for i in range(3):
            for j in range(4):
                if number == (i * 4) + j:
                    self.tiles[(i * 4) + j].setStyleSheet("QLabel { background-color: rgba(" + self.colors_tiles[(i * 4) + j] + ", 255); }")
                    self.tiles[(i * 4) + j].setText(str(x) + "\n" + str(y))
                else:
                    self.tiles[(i * 4) + j].setStyleSheet("QLabel { background-color: rgba(" + self.colors_tiles[(i * 4) + j] + ", 30); }")


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

        print("data:")
        print("left: ", self.left_limit)
        print("right: ", self.right_limit)
        print("top: ", self.top_limit)
        print("bottom: ", self.bottom_limit)
        print("middleh: ", self.middleh_limit)
        print("middlev: ", self.middlev_limit)
        print("contrast: ", self.contrastThreshold)
        print("end data")

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


