import sys
import numpy as np
# import cv2

try:
    import PySpin
    import EasyPySpin
    FLIR_DETECTED = True
    from cameras.FLIRCamera import FLIRCamera
except ImportError as e:
    print('PySpin module not detected')
    FLIR_DETECTED = False

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt
# from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from UI.MainWindow import Ui_MainWindow
from UI.CameraWindow import Ui_CameraWindow

from threads import CameraThread, WorkerThread
from cameras.WebCamera import WebCamera
from cameras.NetworkCamera import NetworkCamera
from cameraWidget import CameraWidget

class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    def __init__(self, camera):
        super().__init__()
        self.setupUi(self)

        self.window_width = self.frameGeometry().width()
        self.window_height = self.frameGeometry().height()

        self.cameraGrid = QtWidgets.QGridLayout()
        self.cameraGrid.setContentsMargins(0,0,0,0)
        self.setLayout(self.cameraGrid)

        #TODO: Implement ability to add multiple camera widgets
        cam0 = CameraWidget(self.window_width, self.window_height, camera, type(camera).__name__, aspect_ratio=True)
        self.cameraGrid.addWidget(cam0)

    def startRecording(self, writer_params):
        widgets = (self.cameraGrid.itemAt(i).widget() for i in range(self.cameraGrid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.startWriter(writer_params)

    def showEvent(self, event):
        super().showEvent(event)

        widgets = (self.cameraGrid.itemAt(i).widget() for i in range(self.cameraGrid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.startDisplay()

        # if can_exit:
        event.accept() # let the window close
        # else:
        #     event.ignore()

    def closeEvent(self, event):
        super().closeEvent(event)

        widgets = (self.cameraGrid.itemAt(i).widget() for i in range(self.cameraGrid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.stopDisplay()

        # if can_exit:
        event.accept() # let the window close
        # else:
        #     event.ignore()

    def startDisplay(self):
        pass

    def stopDisplay(self):  
        pass

    def clearLayout(self):
        while self.cameraGrid.count() > 0:
            camWidget = self.cameraGrid.takeAt(0).widget()
            if camWidget is not None:
                if camWidget.recording:
                    camWidget.stopWriter()
                camWidget.stopCameraThread()
                camWidget.deleteLater()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Set geometry relative to screen
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (sg.width() - self.width()) // 2
        y_pos = (sg.height() - self.height()) // 2
        self.move(x_pos, y_pos)
        # self.setGeometry(x_position, y_position, window_width, window_height)

        self.cameras = {}
        self.cameraWindows = {}

        self.populate_available_cameras()

        # Open and show camera feed but don't record
        self.displayButton.clicked.connect(self.show_camera_window)

        # Open, show and record camera feed into video
        self.recordButton.clicked.connect(self.record_camera_window)

        # Close camera feed (stop recording) and window
        self.stopButton.clicked.connect(self.close_camera_window)


    def populate_available_cameras(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Find all FLIR cameras
        if FLIR_DETECTED:
            flirCams = FLIRCamera.getAllCameras()
            for serialNumber, camera in flirCams.items():
                layout.addWidget(QtWidgets.QCheckBox(serialNumber))
                self.cameras[serialNumber] = camera
                self.cameraWindows[serialNumber] = None
        
        # Find all web cameras
        webCams = WebCamera.getAllCameras()
        for name, camera in webCams.items():
            layout.addWidget(QtWidgets.QCheckBox(name))
            self.cameras[name] = camera
            self.cameraWindows[name] = None

        self.camList.setLayout(layout)
    
    def checkBoxState(self):
        updatedList = {}

        for widget in self.camList.children():
            if isinstance(widget, QtWidgets.QCheckBox):
                serialNumber = widget.text()
                updatedList[serialNumber] = widget.isChecked()
        
        return updatedList

    def show_camera_window(self):
        updatedList = self.checkBoxState()
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        screen_width = sg.width()
        for index, (serial, value) in enumerate(updatedList.items()):
            print(index, serial, value)
            if value is True:
                if self.cameraWindows[serial] is None:
                    window = CameraWindow(self.cameras[serial])
                    x_pos = min(window.width() * index, screen_width - window.width())
                    y_pos = (window.height() // 2) * (index * window.width() // screen_width)
                    window.move(x_pos,y_pos)
                    window.show()

                    self.cameraWindows[serial] = window
                else:
                    self.cameraWindows[serial].show()

    def record_camera_window(self):
        self.show_camera_window()

        updatedList = self.checkBoxState()

        for serial, value in updatedList.items():
            if value is True:
                if self.cameraWindows[serial] is not None:
                    params = {}
                    self.cameraWindows[serial].startRecording(writer_params=params)

        # params = {"-vcodec": "libx264", "-crf": 0, "-preset": "fast"}
        


    def close_camera_window(self):
        updatedList = self.checkBoxState()

        for serial, value in updatedList.items():
            if value is True:
                if self.cameraWindows[serial] is not None:
                    self.cameraWindows[serial].clearLayout()
                    self.cameraWindows[serial].deleteLater()
                    self.cameraWindows[serial] = None
