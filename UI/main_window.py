import sys
import numpy as np
import time

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from UI.design.Ui_MainWindow import Ui_MainWindow
from UI.camera_window import CameraWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, camera_types = []):
        super().__init__()
        self.setupUi(self)

        # Set geometry relative to screen
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (sg.width() - self.width()) // 2
        y_pos = 2 * (sg.height() - self.height()) // 3
        self.move(x_pos, y_pos)

        self.cameras = {}
        self.camera_windows = {}

        self.camera_types = camera_types
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
        for row, camera in enumerate(self.cameras.values()):
            self.cam_stats.setItem(row, 0, QtWidgets.QTableWidgetItem(camera.getName()))
            self.cam_stats.setItem(row, 1, QtWidgets.QTableWidgetItem(str(camera.frames_acquired)))
            if hasattr(camera, "frames_dropped"):
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem(str(camera.frames_dropped)))
            else:
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem("N/A"))

    def populate_available_cameras(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        for camera_cls in self.camera_types:
            cam_list = camera_cls.getAvailableCameras()
            for cam in cam_list:
                layout.addWidget(QtWidgets.QCheckBox(cam.cameraID))
                self.cameras[cam.cameraID] = cam
                self.camera_windows[cam.cameraID] = None

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

        # if FLIR_DETECTED and FLIRCamera._SYSTEM is not None:
        #     FLIRCamera._SYSTEM.ReleaseInstance()

        event.accept() # let the window close
