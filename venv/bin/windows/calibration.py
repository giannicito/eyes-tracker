import cv2
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QTransform, QColor, QPainter
from PyQt5.QtCore import pyqtSlot
import classes.processes as processes
from windows.testing import TestingWindow
import os
import numpy as np
import threading

class CalibrationWindow(QWidget):
    def __init__(self, parent=None):
        super(CalibrationWindow, self).__init__(parent)

        # initialize variables
        self.width = parent.width
        self.height = parent.height

        self.parent = parent

        self.targetPoint = QLabel("", self)
        self.targetPoint.setGeometry(int((self.width - 50) / 2), int((self.height - 50) / 2), 50, 50)

        self.leftEye = QLabel("Left Eye", self)
        self.leftEye.setGeometry(int((self.width - 550) / 2), 70, 200, 75)

        self.leftEyeBW = QLabel("Left Eye BW", self)
        self.leftEyeBW.setGeometry(int((self.width - 550) / 2), 200, 200, 75)

        self.rightEye = QLabel("Right Eye", self)
        self.rightEye.setGeometry(int((self.width - 550) / 2) + 350, 70, 200, 75)

        self.rightEyeBW = QLabel("Right Eye BW", self)
        self.rightEyeBW.setGeometry(int((self.width - 550) / 2) + 350, 200, 200, 75)

        self.thresholdTitle = QLabel("Keep your head and your eyes straight forward the blue point", self)
        self.thresholdTitle.setGeometry(int(self.width / 2) - 250, 350, 500, 30)
        self.thresholdTitle.setAlignment(Qt.AlignCenter)

        self.thresholdTitle = QLabel("Threshold Contrast", self)
        self.thresholdTitle.setGeometry(int(self.width / 2) - 125, 420, 250, 30)
        self.thresholdTitle.setAlignment(Qt.AlignCenter)

        self.contrastThreshold = QSlider(Qt.Horizontal, self)
        self.contrastThreshold.setGeometry(int(self.width / 2) - 125, 450, 250, 25)
        self.contrastThreshold.setMaximum(150)
        self.contrastThreshold.setValue(70)

        self.calibButton = QPushButton('Start Calibration', self)
        self.calibButton.setGeometry(int(self.width / 2) - 100, 500, 200, 30)
        self.calibButton.clicked.connect(self.startCalibration)

        self.calibButton_clicked = False

        self.testButton = QPushButton('Start Testing', self)
        self.testButton.setGeometry(int(self.width / 2) - 100, 550, 200, 30)
        self.testButton.clicked.connect(self.startTesting)

        self.click_detection = 0
        self.eye_padding = 2
        self.flag = 0
        self.thresh = 0.25
        self.pupil_pos = []
        self.trackLeftEye = False

        #calibration
        self.calibrated = 0
        self.point_detection = -1
        self.dir_pos = []
        self.point_pos = []

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.old_face = None
        self.capture = cv2.VideoCapture(0)

        self.circle = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "../image", "circle.png"))
        self.getArrowPixmap(self.circle, "goal-point", [int((self.width - 50) / 2), int((self.height - 75) / 2)], color=QColor(0, 0, 255, 255))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start()

    def startCalibration(self):
        self.calibButton.setEnabled(False)
        self.getArrowPixmap(self.circle, "goal-point", [0, 0])
        self.point_detection = 0

    def startTesting(self):
        self.testButton.setEnabled(False)
        self.parent.Window = TestingWindow(self.parent)
        self.parent.setWindowTitle("Testing Window")
        self.parent.setCentralWidget(self.parent.Window)
        self.parent.show()

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

    def turnOnDirectionArrow(self, p, button,  degree):
        #update status
        pixmap = p.copy()

        if degree != 0:
            t = QTransform()
            t.rotate(degree)
            pixmap = pixmap.transformed(t)

        mask = pixmap.createMaskFromColor(QColor(0, 0, 0), Qt.MaskOutColor)

        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setPen(QColor(255, 0, 0, 255))
        p.drawPixmap(pixmap.rect(), mask, mask.rect())
        p.end()
        self.display_image(None, button, pixmap)

    def update_frame(self):
        _, frame = self.capture.read()
        frame = cv2.flip(frame, 1)


        clahe = cv2.createCLAHE(clipLimit=7.0, tileGridSize=(8, 8))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = clahe.apply(gray)
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
            le_direction, le_bw, le_n = processes.detect_eye_direction(frame, gray, [36, 37, 38, 39, 40, 41], landmarks, self.contrastThreshold.value())
            re_direction, re_bw, re_n = processes.detect_eye_direction(frame, gray, [42, 43, 44, 45, 46, 47], landmarks, self.contrastThreshold.value())

            hor_dir = (le_direction + re_direction) / 2
            ver_dir = processes.getEyeTopPosition([37, 38, 41, 40], landmarks)

            print(hor_dir)

            init_limit = 5

            if self.point_detection >= 0:
                if self.point_detection < init_limit:
                    self.point_detection += 1
                elif self.point_detection == init_limit:
                    self.point_detection += 1

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)

                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(255, 215, 0, 255))
                elif self.point_detection < init_limit + 10:
                    self.dir_pos.append([hor_dir, ver_dir])
                    self.point_detection += 1
                elif self.point_detection == init_limit + 10:
                    self.point_detection += 1
                    final_pos = processes.findProbablePos(self.dir_pos)
                    print(final_pos)
                    self.point_pos.append(final_pos)

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)

                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(0, 255, 0, 255))

                    self.dir_pos = []
                elif self.point_detection < init_limit + 15:
                    self.point_detection += 1
                else:
                    self.point_detection = 0
                    self.calibrated += 1

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)
                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(255, 0, 0, 255))

                    if self.calibrated >= 9:
                        print("all finished")
                        self.point_detection = -1

                        left = (self.point_pos[0][0] + self.point_pos[1][0] + self.point_pos[2][0]) / 3
                        top = (self.point_pos[0][1] + self.point_pos[3][1] + self.point_pos[6][1]) / 3
                        right = (self.point_pos[6][0] + self.point_pos[7][0] + self.point_pos[8][0]) / 3
                        down = (self.point_pos[2][1] + self.point_pos[5][1] + self.point_pos[8][1]) / 3
                        middle_h = (self.point_pos[1][1] + self.point_pos[4][1] + self.point_pos[7][1]) / 3
                        middle_v = (self.point_pos[3][0] + self.point_pos[4][0] + self.point_pos[5][0]) / 3

                        print("left: " + str(left))
                        print("right: " + str(right))
                        print("top: " + str(top))
                        print("down: " + str(down))
                        print("middle_h: " + str(middle_h))
                        print("middle_V: " + str(middle_v))

                        self.saveCalibrationData([left, right, top, down, middle_h, middle_v])


            self.display_image(le_n, "left-eye")
            self.display_image(le_bw, "left-eye-contrast")

            self.display_image(re_n, "right-eye")
            self.display_image(re_bw, "right-eye-contrast")

        #cv2.imshow("face", frame)

    def saveCalibrationData(self, data):
        f = open("./conf/calibration.dat", "w+")

        for i in range(len(data)):
            f.write(str(data[i]) + ",")

        f.write(str(self.contrastThreshold.value()))

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


