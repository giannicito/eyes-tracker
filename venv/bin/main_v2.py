from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import numpy
import pyautogui
from tkinter import *


def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def leftEyeDetection(frame, mousex, mousey, arr):
    """
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_frame = cv2.GaussianBlur(gray_frame, (7, 7), 0)
    _, threshold = cv2.threshold(gray_frame, 43, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # avoid small area / noise
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)

        #cv2.drawContours(threshold, [cnt], -1, (0, 0, 255), 3)
        centerx = x + (w / 2)
        centery = y + (h / 2)
        cv2.circle(frame, (int(centerx), int(centery)), 3, (0, 255, 0), 1)

        # make mouse follow the eye
        #mousex, mousey = MouseFollowTheEye(centerx, centery, mousex, mousey)

        #cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 1)
        #cv2.line(gray_frame, (x + int(w / 2), 0), (x + int(w / 2), height), (0, 255, 0), 2)
        #cv2.line(gray_frame, (0, y + int(h / 2)), (width, y + int(h / 2)), (0, 255, 0), 2)
        break
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    _, threshold = cv2.threshold(gray, 33, 255, cv2.THRESH_BINARY_INV)
    img = cv2.erode(threshold, None, iterations=2)
    img = cv2.dilate(img, None, iterations=4)
    img = cv2.medianBlur(img, 5)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    cx = 0
    cy = 0
    # --------- checking for 2 contours found or not ----------------#
    if len(contours) == 2:
        # img = cv2.drawContours(roi, contours, 1, (0,255,0), 3)
        # ------ finding the centroid of the contour ----------------#
        M = cv2.moments(contours[1])
        # print M['m00']
        # print M['m10']
        # print M['m01']

        (x, y, w, h) = cv2.boundingRect(contours[1])
        min = w
        if w > h:
            min = h

        #print("contours:\n", contours[1])
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            cv2.line(frame, (cx, cy), (cx, cy), (0, 0, 255), 3)
            #cv2.circle(img, (cx, cy), min, (0, 0, 255), -1)
    # -------- checking for one countor presence --------------------#
    elif len(contours) == 1:
        # img = cv2.drawContours(roi, contours, 0, (0,255,0), 3)

        # ------- finding centroid of the countor ----#
        M = cv2.moments(contours[0])

        (x, y, w, h) = cv2.boundingRect(contours[0])
        min = w
        if w > h:
            min = h
        #print("contours:\n", contours[0])
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            # print cx,cy
            #cv2.circle(img, (cx, cy), min, (0, 0, 255), -1)
            cv2.line(frame, (cx, cy), (cx, cy), (0, 0, 255), 3)
    else:
        print("iris not detected")

    # print ("cx: ", cx, "\ncy: ", cy)
    ran = arr[1] - arr[0]
    mid = ran / 2
    if cx < mid:
        print("looking left")
    elif cx > mid:
        print("looking right")
    """
    rany = arr[3] - arr[2]
    midy = rany / 2
    if cy < midy:
        print("looking down")
    elif cy > midy:
        print("looking up")"""

    return frame, img, cx, cy


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


def create_circle(x, y, r, canvasName): #center coordinates, radius
    x0 = x - r
    y0 = y - r
    x1 = x + r
    y1 = y + r
    return canvasName.create_oval(x0, y0, x1, y1)


pyautogui.FAILSAFE = False
mousex = -1
mousey = -1
thresh = 0.25
frame_check = 15
eye_padding = 5

pupil_pos = []
"""
root = Tk()
root.overrideredirect(True)
root.overrideredirect(False)
root.attributes('-fullscreen',True)
w = root.winfo_width()
h = root.winfo_height()

canvas = Canvas(width=w, height=h)
canvas.pack()

#create_circle(0, 0, 20, canvas)
canvas.create_oval(3, 3, 53, 53)
canvas.create_oval(3, h - 54, 53, h - 4)
canvas.create_oval(w - 53, 3, w - 3, 53)
canvas.create_oval(w - 54, h - 54, w - 4, h - 4)"""


# initializing the mouse to the center position


detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Dat file is the crux of the code

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
cap = cv2.VideoCapture(0)
flag = 0
while True:
    #root.update_idletasks()
    #root.update()
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    frame = imutils.resize(frame, width=700)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    subjects = detect(gray, 0)

    eyes_frame = frame.copy()

    LeftEyeArr = [0, 0, 0, 0]

    #contours, hierarchy = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for subject in subjects:
        shape = predict(gray, subject)
        shape = face_utils.shape_to_np(shape)  # converting to NumPy Array
        leftEye = shape[rStart:rEnd]
        rightEye = shape[lStart:lEnd]

        print(leftEye)

        # left eye capture
        # trying to show just the left end
        LeftEyeArr = [leftEye[0][0], leftEye[3][0], leftEye[1][1], leftEye[4][1]]

        leftEAR = eye_aspect_ratio(leftEye)
        rightEAR = eye_aspect_ratio(rightEye)
        ear = (leftEAR + rightEAR) / 2.0
        leftEyeHull = cv2.convexHull(leftEye)
        rightEyeHull = cv2.convexHull(rightEye)
        cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
        if ear < thresh:
            flag += 1
            #print (flag)
            if flag >= frame_check:
                cv2.putText(frame, "****************ALERT!****************", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(frame, "****************ALERT!****************", (10, 325),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # print ("Drowsy")
        else:
            flag = 0

    check = True
    for val in LeftEyeArr:
        if val == 0:
            check = False

    if check is True:
        roi = eyes_frame[LeftEyeArr[2] - eye_padding: LeftEyeArr[3] + eye_padding, LeftEyeArr[0] - eye_padding: LeftEyeArr[1] + eye_padding]
        roi, bw, posx, posy = leftEyeDetection(roi, mousex, mousey, LeftEyeArr)
        #pupil_pos.append([posx, posy])

        if len(pupil_pos) == 5:
            mousex, mousey = MoveMouse(pupil_pos, mousex, mousey, 5)
            pupil_pos = []
        cv2.imshow("Left Eye", roi)
        cv2.imshow("Black and White Eye", bw)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cv2.destroyAllWindows()
cap.stop()