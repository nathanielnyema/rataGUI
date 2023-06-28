import sys
import numpy as np
import time

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from UI.design.Ui_MainWindow import Ui_MainWindow
from UI.camera_window import CameraWindow


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, camera_types = [], plugins = []):
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

        self.plugins = plugins
        self.populate_plugin_list()

        # Open, show and record camera feed into video
        self.start_button.clicked.connect(self.record_camera_window)

        # Open and show camera feed but don't record
        self.pause_button.clicked.connect(self.show_camera_window)

        # Close camera feed (stop recording) and window
        self.stop_button.clicked.connect(self.close_camera_window)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_camera_stats)
        self.update_timer.start(500)


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
        self.cam_list.clear()
        self.cam_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.cam_list.itemDoubleClicked["QListWidgetItem*"].connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for camera_cls in self.camera_types:
            cam_list = camera_cls.getAvailableCameras()
            for cam in cam_list:
                # TODO: use name instead and preserve checked state
                item = QtWidgets.QListWidgetItem(cam.getName())
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.cam_list.addItem(item)
                self.cameras[cam.getName()] = cam
                self.camera_windows[cam.getName()] = None

    def populate_plugin_list(self):
        self.plugin_list.clear()
        self.plugin_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.plugin_list.itemDoubleClicked["QListWidgetItem*"].connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for plugin in self.plugins:
            item = QtWidgets.QListWidgetItem(plugin.__name__)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.plugin_list.addItem(item)
    
    def checkBoxState(check_list: QtWidgets.QListWidget):
        check_boxes = {}

        for idx in range(check_list.count()):
            item = check_list.item(idx)
            check_boxes[item.text()] = (item.checkState() == Qt.CheckState.Checked)

        return check_boxes

    def show_camera_window(self):
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        screen_width = sg.width()

        for idx in range(self.cam_list.count()):
            item = self.cam_list.item(idx)
            if item.checkState() == Qt.CheckState.Checked:
                camID = item.text()
                if self.camera_windows[camID] is None:
                    window = CameraWindow(camera=self.cameras[camID])
                    x_pos = min(window.width() * idx, screen_width - window.width())
                    y_pos = (window.height() // 2) * (idx * window.width() // screen_width)
                    window.move(x_pos,y_pos)
                    window.show()

                    self.camera_windows[camID] = window
                else:
                    self.camera_windows[camID].show()

    def record_camera_window(self):
        self.show_camera_window()

        for idx in range(self.cam_list.count()):
            item = self.cam_list.item(idx)
            if item.checkState() == Qt.CheckState.Checked:
                camID = item.text()
                if self.camera_windows[camID] is not None:
                    params = {"-vcodec": "libx264", "-crf": "28", "-preset": "ultrafast"}
                    self.camera_windows[camID].startWriter(output_params=params)

    def close_camera_window(self):
        for idx in range(self.cam_list.count()):
            item = self.cam_list.item(idx)
            camID = item.text()
            if item.checkState() == Qt.CheckState.Checked and self.camera_windows[camID] is not None:
                cam_window = self.camera_windows[camID]
                self.camera_windows[camID] = None
                if cam_window.recording:
                    cam_window.stopWriter()
                cam_window.stopCameraThread()
                cam_window.deleteLater()

    def closeEvent(self, event):
        for cam_window in self.camera_windows.values():
            if cam_window is not None:
                if cam_window.recording:
                    cam_window.stopWriter()
                cam_window.stopCameraThread()
                cam_window.deleteLater()
        # Wait for threads to stop
        time.sleep(0.5)

        # Release camera-specific resources
        for cam_type in self.camera_types:
            cam_type.releaseResources()

        event.accept() # let the window close
