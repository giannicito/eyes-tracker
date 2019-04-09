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

        pyautogui.FAILSAFE = False

        # initialize variables
        self.mousex = -1
        self.mousey = -1
        self.frame_check = 15
        self.eye_padding = 2
        self.flag = 0
        self.thresh = 0.25
        self.pupil_pos = []
        self.trackLeftEye = False

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(2)

        self.top = self.down = self.left = self.right = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "image", "arrow.png"))
        self.circle = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "image", "circle.png"))

        self.getArrowPixmap(self.top, "top-arrow", degree=-90)
        self.getArrowPixmap(self.down, "down-arrow", degree=90)
        self.getArrowPixmap(self.left, "left-arrow", degree=180)
        self.getArrowPixmap(self.right, "right-arrow", degree=0)
        self.getArrowPixmap(self.circle, "center-circle", color=QColor(255, 0, 0, 255))

        self.directions_status = [1, 0, 0, 0, 0]

    def getArrowPixmap(self, p, identifier,  degree=0, color=QColor(170, 170, 170, 80)):
        pixmap = p.copy()
        if degree != 0:
            t = QTransform()
            t.rotate(degree)
            pixmap = pixmap.transformed(t)

        mask = pixmap.createMaskFromColor(QColor(0, 0, 0), Qt.MaskOutColor)

        pixmap.fill(Qt.transparent)
        p = QPainter(pixmap)
        p.setPen(color)
        p.drawPixmap(pixmap.rect(), mask, mask.rect())
        p.end()
        self.display_image(None, identifier, pixmap)

    def turnOnDirectionArrow(self, p, identifier,  degree=0):
        #update status
        check = 0
        ids = ["center-circle", "left-arrow", "right-arrow", "top-arrow", "down-arrow"]
        for i in range (len(self.directions_status)):
            if self.directions_status[i] == 1:
                # reset active directions status to 0
                if i == 0 and identifier != "center-circle":
                    self.getArrowPixmap(self.circle, "center-circle")
                    check = 1
                elif i == 1 and identifier != "left-arrow":
                    self.getArrowPixmap(self.left, "left-arrow", degree=180)
                    check = 1
                elif i == 2 and identifier != "right-arrow":
                    self.getArrowPixmap(self.right, "right-arrow", degree=0)
                    check = 1
                elif i == 3 and identifier != "top-arrow":
                    self.getArrowPixmap(self.top, "top-arrow", degree=-90)
                    check = 1
                elif i == 4 and identifier != "down-arrow":
                    self.getArrowPixmap(self.down, "down-arrow", degree=90)
                    check = 1

                if check == 1:
                    self.directions_status[i] = 0
                    break

        pixmap = p.copy()
        if check == 1:
            # set the new direction status active
            for i in range(5):
                if ids[i] == identifier:
                    self.directions_status[i] = 1

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
            self.display_image(None, identifier, pixmap)

    def update_frame(self):
        _, frame = self.capture.read()
        frame = cv2.flip(frame, 1)
        frame = imutils.resize(frame, width=700)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        subjects = self.detector(gray, 0)

        eye_frame = frame.copy()

        LeftEyeArr = [0, 0, 0, 0]
        RightEyeArr = [0, 0, 0, 0]

        for subject in subjects:
            shape = self.predict(gray, subject)
            shape = face_utils.shape_to_np(shape)
            leftEye = shape[self.rshape[0]: self.rshape[1]]
            rightEye = shape[self.lshape[0]: self.lshape[1]]

            # left eye capture
            # trying to show just the left end
            LeftEyeArr = [leftEye[0][0], leftEye[3][0], leftEye[1][1], leftEye[4][1]]
            RightEyeArr = [rightEye[0][0], rightEye[3][0], rightEye[1][1], rightEye[4][1]]

            leftEAR = processes.eye_aspect_ratio(leftEye)
            rightEAR = processes.eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            if ear < self.thresh:
                self.flag += 1
                print(self.flag)
                if self.flag >= self.frame_check:
                    cv2.putText(frame, "****************EYES CLOSED!****************", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, "****************EYES CLOSED!****************", (10, 325),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                self.flag = 0

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


        # Detect and track eyes
        lcheck, lframe, bwlframe, lpos = processes.getEyeFrames(eye_frame, LeftEyeArr, self.eye_padding, self.leftEyeCheckbox.isChecked(), self.leftEyeThreshold.value())
        rcheck, rframe, bwrframe, rpos = processes.getEyeFrames(eye_frame, RightEyeArr, self.eye_padding, self.rightEyeCheckbox.isChecked(), self.rightEyeThreshold.value())

        if lcheck is True:
            self.display_image(lframe, "left-eye")
            self.display_image(bwlframe, "left-eye-contrast")

            if self.leftEyeCheckbox.isChecked():
                if lpos == 0:
                    #center
                    self.turnOnDirectionArrow(self.circle, "center-circle")
                elif lpos == 1:
                    #left
                    self.turnOnDirectionArrow(self.left, "left-arrow", degree=180)
                elif lpos == 2:
                    #right
                    self.turnOnDirectionArrow(self.right, "right-arrow", degree=0)
                elif lpos == 3:
                    #top
                    self.turnOnDirectionArrow(self.top, "top-arrow", degree=-90)
                elif lpos == 4:
                    #down
                    self.turnOnDirectionArrow(self.down, "down-arrow", degree=90)


        if rcheck is True:
            self.display_image(rframe, "right-eye")
            self.display_image(bwrframe, "right-eye-contrast")

            if self.rightEyeCheckbox.isChecked():
                if rpos == 0:
                    #center
                    self.turnOnDirectionArrow(self.circle, "center-circle")
                elif rpos == 1:
                    #left
                    self.turnOnDirectionArrow(self.left, "left-arrow", degree=180)
                elif rpos == 2:
                    #right
                    self.turnOnDirectionArrow(self.right, "right-arrow", degree=0)
                elif rpos == 3:
                    #top
                    self.turnOnDirectionArrow(self.top, "top-arrow", degree=-90)
                elif rpos == 4:
                    #down
                    self.turnOnDirectionArrow(self.down, "down-arrow", degree=90)

        self.display_image(frame, "face")

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


def MouseFollowTheEye(x, y, mousex, mousey):
    if mousex == -1 or mousey == -1:
        mousex = x
        mousey = y

    message = ""
    next_x = 0
    next_y = 0
    movement = 5

    if x - mousex == 0 and y - mousey == 0:
        message += "stop "

    if x - mousex < 0:
        message += "right "
        next_x += movement

    if x - mousex > 0:
        message += "left "
        next_x -= movement

    if y - mousey < 0:
        message += "down "
        next_y -= movement

    if y - mousey > 0:
        message += "up "
        next_y += movement

    pyautogui.moveRel(next_x, next_y)

    print(message)

    return x, y


def MoveMouse(pupil_pos, mousex, mousey, nsamples):
    x = 0.0
    y = 0.0
    for pos in pupil_pos:
        x += pos[0]
        y += pos[1]

    x /= nsamples
    y /= nsamples

    if mousex == -1 or mousey == -1:
        mousex = x
        mousey = y

    message = ""
    next_x = 0
    next_y = 0
    movement = 5

    if x - mousex == 0 and y - mousey == 0:
        message += "stop "

    if x - mousex < 0:
        message += "right "
        next_x += movement

    if x - mousex > 0:
        message += "left "
        next_x -= movement

    """
    if y - mousey < 0:
        message += "down "
        next_y -= movement

    if y - mousey > 0:
        message += "up "
        next_y += movement"""

    pyautogui.moveRel(next_x, next_y)

    print(message)

    return x, y



app = QApplication(sys.argv)
window = CalibrationWindow()
window.setWindowTitle("Calibration Window")
window.show()
sys.exit(app.exec_())
