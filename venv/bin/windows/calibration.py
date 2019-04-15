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

class CalibrationWindow(QWidget):
    def __init__(self, parent=None):
        super(CalibrationWindow, self).__init__(parent)

        # initialize variables
        self.width = parent.width
        self.height = parent.height

        print("w: " + str(self.width))
        print("h: " + str(self.height))

        self.targetPoint = QLabel("", self)
        self.targetPoint.setGeometry(-100, -100, 50, 50)

        self.leftEye = QLabel("Left Eye", self)
        self.leftEye.setGeometry(int((self.width - 550) / 2), 70, 200, 75)

        self.leftEyeBW = QLabel("Left Eye BW", self)
        self.leftEyeBW.setGeometry(int((self.width - 550) / 2), 200, 200, 75)

        self.rightEye = QLabel("Right Eye", self)
        self.rightEye.setGeometry(int((self.width - 550) / 2) + 350, 70, 200, 75)

        self.rightEyeBW = QLabel("Right Eye BW", self)
        self.rightEyeBW.setGeometry(int((self.width - 550) / 2) + 350, 200, 200, 75)

        self.thresholdTitle = QLabel("Threshold Contrast", self)
        self.thresholdTitle.setGeometry(int(self.width / 2) - 125, 400, 250, 30)
        self.thresholdTitle.setAlignment(Qt.AlignCenter)

        self.contrastThreshold = QSlider(Qt.Horizontal, self)
        self.contrastThreshold.setGeometry(int(self.width / 2) - 125, 450, 250, 25)
        self.contrastThreshold.setMaximum(150)
        self.contrastThreshold.setValue(70)

        button = QPushButton('Start Calibration', self)
        button.setGeometry(int(self.width / 2) - 100, 500, 200, 30)
        button.clicked.connect(self.startCalibration)

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

            if blinking_ratio > 5.7:
                if len(self.dir_pos) > 0:
                    del self.dir_pos[-1]
                    self.point_detection -= 1


            # detect eye direction
            le_direction, le_bw, le_n = processes.detect_eye_direction(frame, gray, [36, 37, 38, 39, 40, 41], landmarks, self.contrastThreshold.value())
            re_direction, re_bw, re_n = processes.detect_eye_direction(frame, gray, [42, 43, 44, 45, 46, 47], landmarks, self.contrastThreshold.value())

            hor_dir = (le_direction + re_direction) / 2
            ver_dir = processes.getEyeTopPosition([37, 38, 41, 40], landmarks)

            init_limit = 30

            if self.point_detection >= 0:
                if self.point_detection < init_limit:
                    self.point_detection += 1
                elif self.point_detection == init_limit:
                    self.point_detection += 1

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)
                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(255, 215, 0, 255))
                elif self.point_detection <= init_limit + 50:
                    self.dir_pos.append([hor_dir, ver_dir])
                    self.point_detection += 1
                elif self.point_detection == init_limit + 51:
                    self.point_detection += 1
                    final_pos = processes.findProbablePos(self.dir_pos)
                    print (final_pos)
                    self.point_pos.append(final_pos)

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)
                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(0, 255, 0, 255))

                    self.dir_pos = []
                elif self.point_detection < init_limit + 70:
                    self.point_detection += 1
                else:
                    self.point_detection = 0
                    self.calibrated += 1

                    posx = (int)((self.width - 50) / 2) * (int)(self.calibrated / 3)
                    posy = (int)((self.height - 75) / 2) * (self.calibrated % 3)
                    self.getArrowPixmap(self.circle, "goal-point", [posx, posy], color=QColor(255, 0, 0, 255))

                    if self.calibrated >= 9:
                        print("all finished")
                        self.point_detection = 300

                        self.saveCalibrationData()
                        """left = (self.point_pos[0][0] + self.point_pos[1][0] + self.point_pos[2][0]) / 3
                        top = (self.point_pos[0][1] + self.point_pos[3][1] + self.point_pos[6][1]) / 3
                        right = (self.point_pos[6][0] + self.point_pos[7][0] + self.point_pos[8][0]) / 3
                        down = (self.point_pos[2][1] + self.point_pos[5][1] + self.point_pos[8][1]) / 3
    
                        print("left: " + str(left))
                        print("right: " + str(right))
                        print("top: " + str(top))
                        print("down: " + str(down))"""


            self.display_image(le_n, "left-eye")
            self.display_image(le_bw, "left-eye-contrast")

            self.display_image(re_n, "right-eye")
            self.display_image(re_bw, "right-eye-contrast")

        #self.display_image(frame, "face")

    def saveCalibrationData(self):
        f = open("./conf/calibration.dat", "w+")

        for i in range(9):
            f.write(str(self.point_pos[0][0]) + "," + str(self.point_pos[0][1]) + "\n")

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

    def startCalibration(self):
        self.targetPoint.move(0, 0)
        self.getArrowPixmap(self.circle, "goal-point", [0, 0])

        self.point_detection = 0



