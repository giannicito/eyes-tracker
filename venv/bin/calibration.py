from imutils import face_utils
import imutils
import cv2
import pyautogui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi
from PyQt5.QtGui import QPixmap, QImage, QTransform, QColor, QPainter, QPen, QBrush
import classes.processes as processes
import os
import sys

class CalibrationWindow(QMainWindow):
    def __init__(self):
        super(CalibrationWindow, self).__init__()
        loadUi(os.path.join("guifiles", "calibration_window.ui"), self)
        with open(os.path.join("guifiles", "style.css"), "r") as css:
            self.setStyleSheet(css.read())

        #self.showFullScreen()
        #self.showFullScreen()
        self.showMaximized()
        self.statusBar().hide()

        pyautogui.FAILSAFE = False

        # initialize variables
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()

        print("w: " + str(self.width))
        print("h: " + str(self.height))

        self.click_detection = 0
        self.eye_padding = 2
        self.flag = 0
        self.thresh = 0.25
        self.pupil_pos = []
        self.trackLeftEye = False

        #calibration
        self.calibrated = 0
        self.point_detection = 0
        self.dir_pos = []
        self.point_pos = []

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(2)

        self.circle = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "image", "circle.png"))
        self.getArrowPixmap(self.circle, "goal-point", [0, 0])

    def getArrowPixmap(self, p, identifier, position, color=QColor(255, 0, 0, 255)):
        self.goalPoint.move(position[0], position[1])
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

        if self.trackLeftEye:
            if self.rightEyeCheckbox.isChecked():
                self.leftEyeCheckbox.setChecked(False)
                self.trackLeftEye = False
            else:
                self.leftEyeCheckbox.setChecked(True)
        else:
            if self.leftEyeCheckbox.isChecked():
                self.rightEyeCheckbox.setChecked(False)
                self.trackLeftEye = True
            else:
                self.rightEyeCheckbox.setChecked(True)

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

                    left = (self.point_pos[0][0] + self.point_pos[1][0] + self.point_pos[2][0]) / 3
                    top = (self.point_pos[0][1] + self.point_pos[3][1] + self.point_pos[6][1]) / 3
                    right = (self.point_pos[6][0] + self.point_pos[7][0] + self.point_pos[8][0]) / 3
                    down = (self.point_pos[2][1] + self.point_pos[5][1] + self.point_pos[8][1]) / 3

                    print("left: " + str(left))
                    print("right: " + str(right))
                    print("top: " + str(top))
                    print("down: " + str(down))


            self.display_image(le_n, "left-eye")
            self.display_image(le_bw, "left-eye-contrast")

            self.display_image(re_n, "right-eye")
            self.display_image(re_bw, "right-eye-contrast")

        #self.display_image(frame, "face")

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
                self.goalPoint.setPixmap(pixmap)
                self.goalPoint.setScaledContents(True)




app = QApplication(sys.argv)
window = CalibrationWindow()
window.setWindowTitle("Main Window")
window.show()
sys.exit(app.exec_())
