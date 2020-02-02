import dlib
import cv2
import numpy as np
from math import hypot
import uuid
from gtts import gTTS
from playsound import playsound
import os

def initialize_opencv():
    detect = dlib.get_frontal_face_detector()
    predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    return detect, predict

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

def detect_eye_direction(frame, eye_points, facial_landmarks, threshold_value=70):
    eye_region = np.array([(facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y),
                                (facial_landmarks.part(eye_points[1]).x, facial_landmarks.part(eye_points[1]).y),
                                (facial_landmarks.part(eye_points[2]).x, facial_landmarks.part(eye_points[2]).y),
                                (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y),
                                (facial_landmarks.part(eye_points[4]).x, facial_landmarks.part(eye_points[4]).y),
                                (facial_landmarks.part(eye_points[5]).x, facial_landmarks.part(eye_points[5]).y)], np.int32)

    min_x = np.min(eye_region[:, 0])
    max_x = np.max(eye_region[:, 0])
    min_y = np.min(eye_region[:, 1])
    max_y = np.max(eye_region[:, 1])

    normal_eye = frame[min_y: max_y, min_x: max_x]

    eye = cv2.resize(normal_eye, None, fx=1, fy=1)

    gray_eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)

    # image filtering
    gray_eye = cv2.GaussianBlur(gray_eye, (11, 11), 0)
    gray_eye = cv2.bilateralFilter(gray_eye, 11, 11, 11)

    if threshold_value % 2 == 0:
        threshold_value += 1

    threshold_eye = cv2.adaptiveThreshold(gray_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, threshold_value, 10)

    kernel = np.ones((3, 3), np.uint8)

    #perform erosion
    threshold_eye = cv2.erode(threshold_eye, kernel, iterations=1)

    kernel = np.ones((7, 7), np.uint8)
    #removing noise
    threshold_eye = cv2.morphologyEx(threshold_eye, cv2.MORPH_CLOSE, kernel)

    # inverting the colors, white to black and viceversa
    th, threshold_eye = cv2.threshold(threshold_eye, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
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

def getEyeTopPosition(eye_top_points, landmarks):
    center_top = midpoint(landmarks.part(eye_top_points[0]), landmarks.part(eye_top_points[1]))
    center_bottom = midpoint(landmarks.part(eye_top_points[2]), landmarks.part(eye_top_points[3]))

    return hypot((center_top[0] - center_bottom[0]), (center_top[1] - center_bottom[1]))

def convertTextToAudio(txt, language="en"):
    tts = gTTS(text=txt, lang=language)
    path = "audio/" + str(uuid.uuid4()) + ".mp3"
    tts.save(path)

    playsound(path)
    os.system("start " + path)
    os.remove(path)

def findProbablePos(pos):
    sum_x = 0
    sum_y = 0
    for i in range(len(pos)):
        sum_x += pos[i][0]
        sum_y += pos[i][1]

    sum_x /= len(pos)
    sum_y /= len(pos)

    return [sum_x, sum_y]
