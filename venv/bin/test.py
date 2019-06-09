from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget, QPushButton
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
import sys
import os

class Application(QMainWindow):
    def __init__(self):
        super(Application, self).__init__()

        self.showMaximized()

        self.statusBar().hide()
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()

        self.window = MainWindow(self)
        self.setCentralWidget(self.window)

        self.showMaximized()

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        label = QLabel("SHOW IMAGE", self)
        label.setGeometry((parent.width - 500) / 2, 0, 500, 50)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Calibri", 33, QFont.Normal))

        images = QLabel("", self)
        images.setGeometry((parent.width - 1000) / 2, 55, 1000, 700)
        images.setAlignment(Qt.AlignCenter)
        images.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
        pixmap = QPixmap(os.path.join(os.path.abspath(os.path.dirname(__file__)), "./image", "image.png"))
        images.setPixmap(pixmap)
        images.setScaledContents(True)

        button = QPushButton('Example Button', self)
        button.setGeometry((parent.width - 200) / 2, 760, 200, 30)
        button.clicked.connect(self.buttonAction)

    def buttonAction(self):
        print("button has been clicked")

app = QApplication(sys.argv)
window = Application()
window.setWindowTitle("EyeHelpYou")
sys.exit(app.exec_())



"""import cv2
import dlib
from imutils import face_utils
import numpy as np
from math import hypot
from PyQt5.QtWidgets import QApplication, QMainWindow
import sys

def getEyeRegion(frame, eye_points, landmarks, threshold_value=70):
    eye_region = np.array([(landmarks.part(eye_points[0]).x, landmarks.part(eye_points[0]).y),
                           (landmarks.part(eye_points[1]).x, landmarks.part(eye_points[1]).y),
                           (landmarks.part(eye_points[2]).x, landmarks.part(eye_points[2]).y),
                           (landmarks.part(eye_points[3]).x, landmarks.part(eye_points[3]).y),
                           (landmarks.part(eye_points[4]).x, landmarks.part(eye_points[4]).y),
                           (landmarks.part(eye_points[5]).x, landmarks.part(eye_points[5]).y)], np.int32)

    min_x = np.min(eye_region[:, 0])
    max_x = np.max(eye_region[:, 0])
    min_y = np.min(eye_region[:, 1])
    max_y = np.max(eye_region[:, 1])

    eye = frame[min_y: max_y, min_x: max_x]

    gray_eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)

    # smoothing image
    gray_eye = cv2.GaussianBlur(gray_eye, (31, 31), 0)
    gray_eye = cv2.bilateralFilter(gray_eye, 11, 11, 11)

    if threshold_value % 2 == 0:
        threshold_value += 1

    threshold_eye = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                                          threshold_value, 10)

    kernel = np.ones((3, 3), np.uint8)

    # perform erosion
    threshold_eye = cv2.erode(threshold_eye, kernel, iterations=1)

    kernel = np.ones((7, 7), np.uint8)
    # removing noise
    threshold_eye = cv2.morphologyEx(threshold_eye, cv2.MORPH_CLOSE, kernel)

    # inverting the colors, white to black and viceversa
    th, threshold_eye = cv2.threshold(threshold_eye, 127, 255, cv2.THRESH_BINARY_INV)
    cnts, hierarchy = cv2.findContours(threshold_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(cnts) != 0:
        # find the biggest area among that one found
        c = max(cnts, key=cv2.contourArea)
        # evaluate the center of the contour
        M = cv2.moments(c)
        try:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            center = (int(cX), int(cY))
            cv2.circle(eye, center, 7, (0, 255, 0), 2)
        except:
            cX = -1

        return cX, threshold_eye, eye

    else:
        return -1, threshold_eye, eye


def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)


def getEyeTopDownLooking(eye_points, landmarks):
    center_top = midpoint(landmarks.part(eye_points[0]), landmarks.part(eye_points[1]))
    center_bottom = midpoint(landmarks.part(eye_points[2]), landmarks.part(eye_points[3]))

    return hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))

def get_blinking_ratio(eye_points, facial_landmarks):
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))

    hor_line_lenght = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
    ver_line_lenght = hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))

    ratio = hor_line_lenght / ver_line_lenght
    return ratio


cap = cv2.VideoCapture(0)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)

    r = 800.0 / frame.shape[1]
    dim = (800, int(frame.shape[0] * r))

    # resize the frame according to the previous chosen dimension
    frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces_detected = detector(gray, 0)

    if len(faces_detected) > 0:
        face = faces_detected[0]

        landmarks = predictor(gray, face)
        leye_points = [36, 37, 38, 39, 40, 41]
        reye_points = [42, 43, 44, 45, 46, 47]

        #lCx, bwLeftEye, leftEye = getEyeRegion(frame, leye_points, landmarks)
        #rCx, bwRightEye, rightEye = getEyeRegion(frame, reye_points, landmarks)

        #hor_dir = (lCx + rCx) / 2

        lCy = getEyeTopDownLooking([37, 38, 41, 40], landmarks)
        rCy = getEyeTopDownLooking([43, 44, 46, 47], landmarks)

        ver_dir = (lCy + rCy) / 2

        # Detect blinking
        left_eye_ratio = get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
        right_eye_ratio = get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)
        blinking_ratio = (left_eye_ratio + right_eye_ratio) / 2

        if blinking_ratio > 5.3:
            cv2.putText(frame, "BLINKING", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255))

        #cv2.imshow('Left Eye', leftEye)
        #cv2.imshow('Right Eye', rightEye)

        #cv2.imshow('Thresholded Left Eye', bwLeftEye)
        #cv2.imshow('Thresholded Right Eye', bwRightEye)



    # Display the resulting frame
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()"""

"""
from tkinter import *
from PIL import Image, ImageTk

def show_frame():
    _, frame = cap.read()
    frame = cv2.flip(frame, 1)
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    display1.imgtk = imgtk #Shows frame for display 1
    display1.configure(image=imgtk)
    root.after(1, show_frame)

root = Tk()
cap = cv2.VideoCapture(0)

#Graphics window
imageFrame = Frame(root, width=600, height=500)
imageFrame.grid(row=0, column=0, padx=10, pady=2)

display1 = Label(imageFrame)
display1.grid(row=1, column=0, padx=10, pady=2)  #Display 1

show_frame() #Display

root.mainloop()"""