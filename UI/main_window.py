import sys
import numpy as np
import time

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from UI.design.Ui_MainWindow import Ui_MainWindow
from UI.camera_widget import CameraWidget


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, camera_models = [], plugins = []):
        super().__init__()
        self.setupUi(self)

        # Set geometry relative to screen
        self.screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (self.screen.width() - self.width()) // 2
        y_pos = 2 * (self.screen.height() - self.height()) // 3
        self.move(x_pos, y_pos)

        self.cameras = {}
        self.camera_widgets = {}
        self.camera_models = camera_models
        self.populate_available_cameras()

        # create class name look-up
        self.plugins = {p.__name__ : p for p in plugins}
        self.populate_plugin_list()

        # Open, show and record camera feed into video
        self.start_button.clicked.connect(self.start_camera_widgets)
        self.start_button.setStyleSheet("background-color: darkgreen; color: white; font-weight: bold")

        # Open and show camera feed but don't record
        self.pause_button.clicked.connect(self.pause_camera_widgets)
        self.pause_button.setStyleSheet("background-color: grey; color: white; font-weight: bold")

        # Close camera feed (stop recording) and window
        self.stop_button.clicked.connect(self.stop_camera_widgets)
        self.stop_button.setStyleSheet("background-color: darkred; color: white; font-weight: bold")

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
        for camera_cls in self.camera_models:
            cam_list = camera_cls.getAvailableCameras()
            for cam in cam_list:
                # TODO: use name instead and preserve checked state
                item = QtWidgets.QListWidgetItem(cam.getName())
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.cam_list.addItem(item)
                self.cameras[cam.getName()] = cam
                self.camera_widgets[cam.getName()] = None

    def populate_plugin_list(self):
        self.plugin_list.clear()
        self.plugin_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.plugin_list.itemDoubleClicked["QListWidgetItem*"].connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for name in self.plugins.keys():
            item = QtWidgets.QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.plugin_list.addItem(item)

    def populate_plugin_pipeline(self):
        self.plugin_pipeline.clear()

        # Don't rely on checked state

        checked_cameras = [item.text() for item in  get_checked_items(self.cam_list)]
        self.plugin_pipeline.setRowCount(len(checked_cameras))
        self.plugin_pipeline.setVerticalHeaderLabels(checked_cameras)

        checked_plugins = [item.text() for item in get_checked_items(self.plugin_list)]
        self.plugin_pipeline.setColumnCount(len(checked_plugins))
        self.plugin_pipeline.setHorizontalHeaderLabels(checked_plugins)

        for row in range(self.plugin_pipeline.rowCount()):
            for col in range(self.plugin_pipeline.rowCount()):
                item = QtWidgets.QTableWidgetItem("Active")
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.plugin_pipeline.setItem(row, col, item)

        self.plugin_pipeline.resizeColumnsToContents()

    def start_camera_widgets(self):
        checked_camera_items = get_checked_items(self.cam_list)
        checked_plugin_items = get_checked_items(self.plugin_list)
        # Convert plugin items into corresponding class
        checked_plugins = [self.plugins[item.text()] for item in checked_plugin_items]
        if len(checked_plugins) == 0:
            print("At least one plugin must be selected")
            return

        screen_width = self.screen.width()
        for idx, cam_item in enumerate(checked_camera_items):
            camID = cam_item.text()
            cam_widget = self.camera_widgets[camID]
            if cam_widget is None: # Create new window
                window = CameraWidget(camera=self.cameras[camID], plugins=checked_plugins)
                x_pos = min(window.width() * idx, screen_width - window.width())
                y_pos = (window.height() // 2) * (idx * window.width() // screen_width)
                window.move(x_pos,y_pos)
                self.camera_widgets[camID] = window
                cam_item.setBackground(QtGui.QColorConstants.Green)

            elif cam_widget.paused: # Toggle paused window to resume
                cam_widget.paused = False
                cam_item.setBackground(QtGui.QColorConstants.Green)

            self.camera_widgets[camID].show()
            self.populate_plugin_pipeline()

    def pause_camera_widgets(self):
        for cam_item in get_checked_items(self.cam_list):
            camID = cam_item.text()
            cam_widget = self.camera_widgets[camID]
            if cam_widget is not None:
                cam_widget.paused = True
                cam_item.setBackground(QtGui.QColorConstants.Yellow)

    def stop_camera_widgets(self):
        for cam_item in get_checked_items(self.cam_list):
            camID = cam_item.text()
            cam_widget = self.camera_widgets[camID]
            if cam_widget is not None:
                self.camera_widgets[camID] = None
                cam_widget.close_widget()
                cam_item.setBackground(QtGui.QColorConstants.White)

    def closeEvent(self, event):
        for cam_widget in self.camera_widgets.values():
            if cam_widget is not None:
                cam_widget.close_widget()
        # Wait for threads to stop TODO: More sophisticated way to wait for threads to stop
        time.sleep(0.5)

        # Release camera-specific resources
        for cam_type in self.camera_models:
            cam_type.releaseResources()

        event.accept() # let the window close


def get_checked_items(check_list: QtWidgets.QListWidget) -> list:
    checked = []
    for idx in range(check_list.count()):
        item = check_list.item(idx)
        if item.checkState() == Qt.CheckState.Checked:
            checked.append(item)
    return checked