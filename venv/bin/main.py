from PyQt5.QtWidgets import QApplication, QMainWindow
from windows.calibration import CalibrationWindow
import os
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.showMaximized()

        self.statusBar().hide()
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()

        exists = os.path.isfile("./conf/calibration.dat")
        if exists:
            # Store configuration file values
            self.startInitialWindow()
        else:
            # Keep presets
            self.startCalibrationWindow()

    def startInitialWindow(self):
        print("start initial window")

    def startCalibrationWindow(self):
        self.calibration = CalibrationWindow(self)
        self.setWindowTitle("Calibration Window")
        self.setCentralWidget(self.calibration)
        self.showMaximized()




app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("Main Window")
sys.exit(app.exec_())
