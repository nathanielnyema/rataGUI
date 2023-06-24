import sys
import numpy as np
import time
# import cv2

try:
    import PySpin
    FLIR_DETECTED = True
    from cameras.FLIRCamera import FLIRCamera
except ImportError as e:
    print('PySpin module not detected')
    FLIR_DETECTED = False

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer, QAbstractTableModel
# from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from UI.Ui_MainWindow import Ui_MainWindow
from UI.Ui_CameraWindow import Ui_CameraWindow

from threads import CameraThread, WorkerThread
from cameras.WebCamera import WebCamera
from cameras.NetworkCamera import NetworkCamera
from UI.CameraWidget import CameraWidget

class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    def __init__(self, camera):
        super().__init__()
        self.setupUi(self)

        self.window_width = self.frameGeometry().width()
        self.window_height = self.frameGeometry().height()

        self.camera_grid = QtWidgets.QGridLayout()
        self.camera_grid.setContentsMargins(0,0,0,0)
        self.setLayout(self.camera_grid)

        #TODO: Implement ability to add multiple camera widgets
        cam0 = CameraWidget(self.window_width, self.window_height, camera, type(camera).__name__, aspect_ratio=True)
        self.camera_grid.addWidget(cam0)

    def startRecording(self, writer_params):
        widgets = (self.camera_grid.itemAt(i).widget() for i in range(self.camera_grid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.startWriter(writer_params)

    def clearLayout(self):
        while self.camera_grid.count() > 0:
            cam_widget = self.camera_grid.takeAt(0).widget()
            if cam_widget is not None:
                if cam_widget.recording:
                    cam_widget.stopWriter()
                cam_widget.stopCameraThread()
                cam_widget.deleteLater()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Set geometry relative to screen
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (sg.width() - self.width()) // 2
        y_pos = 2 * (sg.height() - self.height()) // 3
        self.move(x_pos, y_pos)
        # self.setGeometry(x_position, y_position, window_width, window_height)

        self.cameras = {}
        self.camera_windows = {}

        self.populate_available_cameras()

        # Open and show camera feed but don't record
        self.display_button.clicked.connect(self.show_camera_window)

        # Open, show and record camera feed into video
        self.record_button.clicked.connect(self.record_camera_window)

        # Close camera feed (stop recording) and window
        self.stop_button.clicked.connect(self.close_camera_window)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera_stats)
        self.timer.start(500)


    def update_camera_stats(self):
        self.cam_stats.setRowCount(len(self.cameras))
        for row, (id, camera) in enumerate(self.cameras.items()):
            self.cam_stats.setItem(row, 0, QtWidgets.QTableWidgetItem(id))
            self.cam_stats.setItem(row, 1, QtWidgets.QTableWidgetItem(str(camera.frames)))
            if hasattr(camera, "frames_dropped"):
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem(str(camera.frames_dropped)))
            else:
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem("N/A"))

    def populate_available_cameras(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Find all FLIR cameras
        if FLIR_DETECTED:
            flir_cams = FLIRCamera.getAvailableCameras()
            for serial_number, camera in flir_cams.items():
                layout.addWidget(QtWidgets.QCheckBox(serial_number))
                self.cameras[serial_number] = camera
                self.camera_windows[serial_number] = None
        
        # Find all web cameras
        web_cams = WebCamera.getAvailableCameras()
        for name, camera in web_cams.items():
            layout.addWidget(QtWidgets.QCheckBox(name))
            self.cameras[name] = camera
            self.camera_windows[name] = None

        self.cam_list.setLayout(layout)
    
    def checkBoxState(self):
        updated_list = {}

        for widget in self.cam_list.children():
            if isinstance(widget, QtWidgets.QCheckBox):
                serial_number = widget.text()
                updated_list[serial_number] = widget.isChecked()
        
        return updated_list

    def show_camera_window(self):
        updated_list = self.checkBoxState()
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        screen_width = sg.width()
        for index, (serial, value) in enumerate(updated_list.items()):
            if value is True:
                if self.camera_windows[serial] is None:
                    window = CameraWindow(self.cameras[serial])
                    x_pos = min(window.width() * index, screen_width - window.width())
                    y_pos = (window.height() // 2) * (index * window.width() // screen_width)
                    window.move(x_pos,y_pos)
                    window.show()

                    self.camera_windows[serial] = window
                else:
                    self.camera_windows[serial].show()

    def record_camera_window(self):
        self.show_camera_window()

        updated_list = self.checkBoxState()

        for serial, value in updated_list.items():
            if value is True:
                if self.camera_windows[serial] is not None:
                    params = {}
                    self.camera_windows[serial].startRecording(writer_params=params)

        # params = {"-vcodec": "libx264", "-crf": 0, "-preset": "fast"}

    def close_camera_window(self):
        updated_list = self.checkBoxState()

        for serial, value in updated_list.items():
            if value is True and self.camera_windows[serial] is not None:
                self.camera_windows[serial].clearLayout()
                self.camera_windows[serial].deleteLater()
                self.camera_windows[serial] = None

    def closeEvent(self, event):        
        for cam_window in self.camera_windows.values():
            if cam_window is not None:
                cam_window.clearLayout()
                cam_window.deleteLater()
        # Wait for threads to stop
        time.sleep(0.5)

        if FLIR_DETECTED and FLIRCamera._SYSTEM is not None:
            FLIRCamera._SYSTEM.ReleaseInstance()

        event.accept() # let the window close
