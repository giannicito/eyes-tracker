from PyQt5.QtWidgets import QApplication, QMainWindow
from frames.calibration import CalibrationWindow
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.showMaximized()

        self.statusBar().hide()
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()

        # calibration data
        self.calibrationData = [0, 0, 0, 0, 0, 0, 31]

        self.startCalibrationWindow()

    def startCalibrationWindow(self):
        self.calibration = CalibrationWindow(self)
        self.setWindowTitle("Calibration Window")
        self.setCentralWidget(self.calibration)
        self.showMaximized()

app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("EyeHelpYou")
sys.exit(app.exec_())