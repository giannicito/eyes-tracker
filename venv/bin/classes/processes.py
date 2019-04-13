from imutils import face_utils
from scipy.spatial import distance
import imutils
import dlib
import cv2
import numpy as np
from math import hypot


def initialize_opencv():
    detect = dlib.get_frontal_face_detector()
    predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # Dat file is the crux of the code

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]

    return [lStart, lEnd], [rStart, rEnd], detect, predict

def midpoint(p1 ,p2):
    return int((p1.x + p2.x)/2), int((p1.y + p2.y)/2)

def get_blinking_ratio(eye_points, facial_landmarks):
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)
    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))

    hor_line_lenght = hypot((left_point[0] - right_point[0]), (left_point[1] - right_point[1]))
    ver_line_lenght = hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))

    ratio = hor_line_lenght / ver_line_lenght
    return ratio

def detect_eye_direction(frame, gray, eye_points, facial_landmarks, threshold_value=70):
    eye_region = np.array([(facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y),
                                (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(eye_points[1]).y),
                                (facial_landmarks.part(eye_points[2]).x, facial_landmarks.part(eye_points[2]).y),
                                (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y),
                                (facial_landmarks.part(eye_points[4]).x, facial_landmarks.part(eye_points[4]).y),
                                (facial_landmarks.part(eye_points[5]).x, facial_landmarks.part(eye_points[5]).y)], np.int32)
    #cv2.polylines(frame, [left_eye_region], True, (0, 0, 255), 2)

    height, width, _ = frame.shape
    mask = np.zeros((height, width), np.uint8)
    cv2.polylines(mask, [eye_region], True, 255, 2)
    cv2.fillPoly(mask, [eye_region], 255)
    geye = cv2.bitwise_and(gray, gray, mask=mask)

    min_x = np.min(eye_region[:, 0])
    max_x = np.max(eye_region[:, 0])
    min_y = np.min(eye_region[:, 1])
    max_y = np.max(eye_region[:, 1])

    gray_eye = geye[min_y: max_y, min_x: max_x]
    normal_eye = frame[min_y: max_y, min_x: max_x]
    eye = cv2.resize(normal_eye, None, fx=5, fy=5)

    _, threshold_eye = cv2.threshold(gray_eye, threshold_value, 255, cv2.THRESH_BINARY)
    height, width = threshold_eye.shape
    left_side_threshold = threshold_eye[0: height, 0: int(width / 2)]
    left_side_white = cv2.countNonZero(left_side_threshold)

    right_side_threshold = threshold_eye[0: height, int(width / 2): width]
    right_side_white = cv2.countNonZero(right_side_threshold)

    if left_side_white == 0:
        gaze_ratio = 0
    elif right_side_white == 0:
        gaze_ratio = 5
    else:
        gaze_ratio = left_side_white / right_side_white

    return gaze_ratio, threshold_eye, eye

def getEyeTopPosition(eye_top_points, landmarks):
    center_top = midpoint(landmarks.part(eye_top_points[0]), landmarks.part(eye_top_points[1]))
    center_bottom = midpoint(landmarks.part(eye_top_points[2]), landmarks.part(eye_top_points[3]))

    ver_line_lenght = hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))
    return ver_line_lenght

def eye_aspect_ratio(eye):
    A = distance.euclidean(eye[1], eye[5])
    B = distance.euclidean(eye[2], eye[4])
    C = distance.euclidean(eye[0], eye[3])
    ear = (A + B) / (2.0 * C)
    return ear

def getEyeFrames(eye_frame, eyeArr, eye_padding, trackEye, threshold_value, resize_dim=50):
    check = True
    for val in eyeArr:
        if val == 0:
            check = False

    if check is True:
        roi = eye_frame[eyeArr[2] - eye_padding: eyeArr[3] + eye_padding, eyeArr[0] - eye_padding: eyeArr[1] + eye_padding]
        roi = imutils.resize(roi, width=resize_dim)
        roi, bw, pos = EyeDetectionCenter(roi, eyeArr, trackEye, threshold_value)
        return check, roi, bw, pos
    else:
        return check, eye_frame, eye_frame, 0

def EyeDetectionCenter(frame, arr, trackEye, threshold_value):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    _, threshold = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)
    img = cv2.erode(threshold, None, iterations=2)
    img = cv2.dilate(img, None, iterations=4)
    img = cv2.medianBlur(img, 5)
    contours, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    id = 0
    if trackEye:
        cx = 0
        cy = 0
        # --------- checking for 2 contours found or not ----------------#
        if len(contours) == 2:
            M = cv2.moments(contours[1])

            #print("contours:\n", contours[1])
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cv2.line(frame, (cx, cy), (cx, cy), (0, 0, 255), 3)
        # -------- checking for one countor presence --------------------#
        elif len(contours) == 1:
            # img = cv2.drawContours(roi, contours, 0, (0,255,0), 3)

            # ------- finding centroid of the countor ----#
            M = cv2.moments(contours[0])

            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])

                cv2.line(frame, (cx, cy), (cx, cy), (0, 0, 255), 3)
        else:
            print("iris not detected")

        # print ("cx: ", cx, "\ncy: ", cy)
        #ran = arr[1] - arr[0]
        #print("cx: ", cx)
        #print("cy: ", cy)
        #print("left: ", mid - center_range)
        #print("right: ", mid + center_range)
        if trackEye:
            id = drawEyeGrid(frame, cx)
            """
            rany = arr[3] - arr[2]
            midy = rany / 2
            if cy < midy:
                print("looking down")
            elif cy > midy:
                print("looking up")"""

    return frame, img, id

def drawEyeGrid(frame, cx):
    h, w, channels = frame.shape

    ranx = (w / 7)
    # find x lower and higher limit
    xll = int((w / 2) - ranx - (w / 15))
    xhl = int((w / 2) + ranx + (w / 15))
    cv2.line(frame, (xll, 0), (xll, h), (255, 0, 0), 1)
    cv2.line(frame, (xhl, 0), (xhl, h), (255, 0, 0), 1)

    rany = h / 5
    # find y lower and higher limit
    yll = int((h / 2) - rany)
    yhl = int((h / 2) + rany)
    cv2.line(frame, (0, yll), (w, yll), (255, 0, 0), 1)
    cv2.line(frame, (0, yhl), (w, yhl), (255, 0, 0), 1)

    id = 0
    if cx < xll:
        print("looking left")
        id = 1
    elif cx > xhl:
        print("looking right")
        id = 2
    else:
        print("looking center")

    return id
