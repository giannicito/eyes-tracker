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
        loadUi(os.path.join("guifiles", "main_window.ui"), self)
        with open(os.path.join("guifiles", "style.css"), "r") as css:
            self.setStyleSheet(css.read())

        pyautogui.FAILSAFE = False

        # initialize variables
        self.mousex = -1
        self.mousey = -1
        self.click_detection = 0
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

    def turnOnDirectionArrow(self, pixmaps, buttons,  degrees):
        #update status
        ids = ["center-circle", "left-arrow", "right-arrow", "top-arrow", "down-arrow"]
        for i in range(len(self.directions_status)):
            if self.directions_status[i] == 1:
                # reset active directions status to 0
                if i == 0 and "center-circle" not in buttons:
                    self.getArrowPixmap(self.circle, "center-circle")
                    self.directions_status[i] = 0
                elif i == 1 and "left-arrow" not in buttons:
                    self.getArrowPixmap(self.left, "left-arrow", degree=180)
                    self.directions_status[i] = 0
                elif i == 2 and "right-arrow" not in buttons:
                    self.getArrowPixmap(self.right, "right-arrow", degree=0)
                    self.directions_status[i] = 0
                elif i == 3 and "top-arrow" not in buttons:
                    self.getArrowPixmap(self.top, "top-arrow", degree=-90)
                    self.directions_status[i] = 0
                elif i == 4 and "down-arrow" not in buttons:
                    self.getArrowPixmap(self.down, "down-arrow", degree=90)
                    self.directions_status[i] = 0

        # set the new direction status active
        for i in range(5):
            if ids[i] in buttons:
                self.directions_status[i] = 1

        for i in range(len(buttons)):
            pixmap = pixmaps[i].copy()

            if degrees[i] != 0:
                t = QTransform()
                t.rotate(degrees[i])
                pixmap = pixmap.transformed(t)

            mask = pixmap.createMaskFromColor(QColor(0, 0, 0), Qt.MaskOutColor)

            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            p.setPen(QColor(255, 0, 0, 255))
            p.drawPixmap(pixmap.rect(), mask, mask.rect())
            p.end()
            self.display_image(None, buttons[i], pixmap)

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
                self.click_detection += 1

                if self.click_detection == 5:
                    cv2.putText(frame, "BLINKING", (50, 200), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 3)
                    self.click_detection = 0
                    #click

            else:
                self.click_detection = 0


            # detect eye direction
            le_direction, le_bw, le_n = processes.detect_eye_direction(frame, gray, [36, 37, 38, 39, 40, 41], landmarks, self.contrastThreshold.value())
            re_direction, re_bw, re_n = processes.detect_eye_direction(frame, gray, [42, 43, 44, 45, 46, 47], landmarks, self.contrastThreshold.value())

            direction = (le_direction + re_direction) / 2

            left_limit = 0.77
            right_limit = 2.3

            pixmaps = []
            buttons = []
            degrees = []
            center_ = 0
            if direction <= left_limit:
                cv2.putText(frame, "LEFT", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                pixmaps.append(self.left)
                buttons.append("left-arrow")
                degrees.append(180)
            elif left_limit < direction < right_limit:
                cv2.putText(frame, "CENTER", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                center_ = 1
            else:
                cv2.putText(frame, "RIGHT", (50, 100), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                pixmaps.append(self.right)
                buttons.append("right-arrow")
                degrees.append(0)


            top_position = processes.getEyeTopPosition([37, 38, 41, 40], landmarks)
            #print("top_eye: ", top_position)

            if top_position > 10:
                cv2.putText(frame, "TOP", (50, 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                pixmaps.append(self.top)
                buttons.append("top-arrow")
                degrees.append(-90)
            elif top_position <= 7.3 and top_position > 5.7:
                cv2.putText(frame, "DOWN", (50, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                pixmaps.append(self.down)
                buttons.append("down-arrow")
                degrees.append(90)
            else:
                if center_ == 1:
                    center_ = 2

            if center_ == 2:
                pixmaps.append(self.circle)
                buttons.append("center-circle")
                degrees.append(0)

            self.turnOnDirectionArrow(pixmaps, buttons, degrees)

            self.display_image(le_n, "left-eye")
            self.display_image(le_bw, "left-eye-contrast")

            self.display_image(re_n, "right-eye")
            self.display_image(re_bw, "right-eye-contrast")

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
window.setWindowTitle("Main Window")
window.show()
sys.exit(app.exec_())
