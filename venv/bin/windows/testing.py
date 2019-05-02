import cv2
import pyautogui
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QSlider, QPushButton
from PyQt5.QtGui import QPixmap, QImage, QColor, QPainter, QFont
import classes.processes as processes

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

        self.keyboard = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "0",
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
            " "
        ]

        # top bar
        self.topBar = QLabel("", self)
        self.topBar.setGeometry(1, 1, self.width - 2, int(self.height / 5) - 1)
        self.topBar.setAlignment(Qt.AlignLeft)
        self.topBar.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
        self.topBar.setFont(QFont("Calibri", 33, QFont.Bold))

        # first line
        y = int(self.height / 5) + 10
        tile_height = int((self.height - y) / 5) - 6
        for i in range(10):
            label = QLabel(self.keyboard[i], self)
            label.setGeometry(int(self.width / 10) * i + 1, y, int(self.width / 10) - 2, tile_height)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
            label.setFont(QFont("Calibri", 33, QFont.Bold))
            self.tiles.append(label)

        # second line
        y += tile_height + 2
        for i in range(10):
            label = QLabel(self.keyboard[i + 10], self)
            label.setGeometry(int(self.width / 10) * i + 1, y, int(self.width / 10) - 2, tile_height)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
            label.setFont(QFont("Calibri", 33, QFont.Bold))
            self.tiles.append(label)

        # third line
        y += tile_height + 2
        for i in range(9):
            label = QLabel(self.keyboard[i + 20], self)
            label.setGeometry(int(self.width / 9) * i + 1, y, int(self.width / 9) - 2, tile_height)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
            label.setFont(QFont("Calibri", 33, QFont.Bold))
            self.tiles.append(label)

        # fourth line
        y += tile_height + 2
        for i in range(7):
            label = QLabel(self.keyboard[i + 29], self)
            label.setGeometry(int(self.width / 7) * i + 1, y, int(self.width / 7) - 2, tile_height)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
            label.setFont(QFont("Calibri", 33, QFont.Bold))
            self.tiles.append(label)

        # fift line
        y += tile_height + 2
        label = QLabel(self.keyboard[36], self)
        label.setGeometry(int(self.width / 4), y, int(self.width / 2), tile_height)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("QLabel { border: 1px solid rgba(128, 128, 128, 255); }")
        label.setFont(QFont("Calibri", 33, QFont.Bold))
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

        self.blinking = -1
        self.tile = 25

        self.text = ""

        self.change_counter = 0
        self.current_direction = 0

        self.lshape, self.rshape, self.detector, self.predict = processes.initialize_opencv()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(0)

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

        r = 800.0 / frame.shape[1]
        dim = (800, int(frame.shape[0] * r))

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

            self.frame_pos.append([hor_dir, ver_dir])

            if blinking_ratio > 5.7:
                print("br: ", blinking_ratio)
                # probably blinking
                self.change_counter = 1
                if self.blinking >= 0:
                    self.blinking += 1
                    if self.blinking >= 5:
                        print("click")
                        self.addLetter()
                        self.blinking = -1
            else:
                self.blinking = 0

                previous_tile = self.tile

                right_limit = ((self.right_limit - self.middlev_limit) / 2)
                left_limit = ((self.middlev_limit - self.left_limit) / 2)
                top_limit = ((self.top_limit - self.middleh_limit) / 2)
                bottom_limit = ((self.middleh_limit - self.bottom_limit) / 2)

                print(hor_dir)

                if hor_dir >= self.right_limit - right_limit:
                    # right
                    print("right: ", self.right_limit - right_limit)
                    self.getDecision(1)
                elif hor_dir <= self.left_limit + left_limit:
                    # left
                    print("left: ", self.left_limit + left_limit)
                    self.getDecision(2)
                elif ver_dir >= self.top_limit - top_limit:
                    #top
                    print("top: ", self.top_limit - top_limit)
                    self.getDecision(3)
                elif ver_dir <= self.bottom_limit + bottom_limit:
                    #bottom
                    print("bottom: ", self.bottom_limit + bottom_limit)
                    self.getDecision(4)
                else:
                    #center
                    print("center")
                    self.getDecision(0)

                self.tiles[previous_tile].setStyleSheet("QLabel { border: 1px solid rgb(128, 128, 128) }")
                self.tiles[self.tile].setStyleSheet("QLabel { background: rgba(128, 128, 128, 150); border: 1px solid rgb(128, 128, 128) }")


    def getDecision(self, direction):
        if self.current_direction != direction:

            self.change_counter = 1
            self.current_direction = direction

        else:
            # direction is the same of the previous one
            # check if I can move again the tile to the following one
            if self.change_counter >= 5:
                self.tile += self.getMotion(direction)

                if self.tile < 0:
                    self.tile = 36
                elif self.tile >= 37:
                    if direction == 4:
                        self.tile = 4
                    else:
                        self.tile = 0

                self.change_counter = 1

            else:
                self.change_counter += 1

    def getMotion(self, direction):
        if direction == 0:
            # center
            return 0

        elif direction == 1:
            # right
            return 1

        elif direction == 2:
            # left
            return -1

        elif direction == 3:
            # top
            if self.tile < 29:
                # first, second and third lines
                return -10

            elif self.tile >= 29 and self.tile < 36:
                # fourth line
                return -9

            else:
                # fifth line
                return -4

        elif direction == 4:
            # bottom
            if self.tile < 10:
                # first, second and third lines
                return 10

            elif self.tile < 20:
                # second line
                return 9

            elif self.tile < 29:
                # third line
                return 7

            elif self.tile < 36:
                # fourth line
                return 36 - self.tile

            else:
                # fifth line
                return 1


    def addLetter(self):
        self.text += self.keyboard[self.tile]
        self.topBar.setText(self.text)


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


