import sys
import numpy as np
import time

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from UI.design.Ui_MainWindow import Ui_MainWindow
from UI.camera_widget import CameraWidget
from UI.tab_widget import VerticalTabWidget


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

        # Create class name look-up
        self.plugins = {p.__name__ : p for p in plugins}
        self.populate_plugin_list()

        # Create camera widget and start pipeline 
        self.start_button.clicked.connect(self.start_camera_widgets)
        self.start_button.setStyleSheet("background-color: darkgreen; color: white; font-weight: bold")

        # Pause camera and plugin pipeline
        self.pause_button.clicked.connect(self.pause_camera_widgets)
        self.pause_button.setStyleSheet("background-color: grey; color: white; font-weight: bold")

        # Close camera, stop pipeline and delete widget
        self.stop_button.clicked.connect(self.stop_camera_widgets)
        self.stop_button.setStyleSheet("background-color: darkred; color: white; font-weight: bold")

        # Update camera stats occasionally
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
                item.setCheckState(Qt.CheckState.Checked)
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
            item.setCheckState(Qt.CheckState.Checked)
            self.plugin_list.addItem(item)

    def populate_plugin_pipeline(self):
        self.plugin_pipeline.clear()

        self.plugin_pipeline.setRowCount(len(self.camera_widgets))
        # self.plugin_pipeline.setVerticalHeaderLabels(self.camera_widgets.keys())

        self.plugin_pipeline.setColumnCount(len(self.plugins))
        # self.plugin_pipeline.setHorizontalHeaderLabels(self.plugins)

        # for row, widget in enumerate(self.camera_widgets.values()):
        #     if widget is not None:
        #         for col, plugin in enumerate()

        active_camera_names = []
        plugin_names = []
        for row, (camID, widget) in enumerate(self.camera_widgets.items()):
            if widget is not None:
                active_camera_names.append(camID)
                for col, plugin in enumerate(widget.plugins):
                    item = QtWidgets.QTableWidgetItem()
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.plugin_pipeline.setItem(row, col, item)
                    if plugin.active:
                        item.setText("Active")
                        item.setCheckState(Qt.CheckState.Checked)
                        
                    else:
                        item.setText("Paused")
                        item.setCheckState(Qt.CheckState.Unchecked)

                    if row == 0:
                        plugin_names.append(type(plugin).__name__)
        
        # Re-adjust table to size
        self.plugin_pipeline.setRowCount(len(active_camera_names))
        self.plugin_pipeline.setVerticalHeaderLabels(active_camera_names)
        self.plugin_pipeline.setColumnCount(len(plugin_names))
        self.plugin_pipeline.setHorizontalHeaderLabels(plugin_names)

        # self.plugin_pipeline.cellChanged.connect()
        self.plugin_pipeline.resizeColumnsToContents()

    def pause_camera_plugin(self, row, column):
        # self.cameras
        pass


    def populate_camera_properties(self):
        pass


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
            if cam_widget is None: # Create new widget
                widget = CameraWidget(camera=self.cameras[camID], plugins=checked_plugins)
                x_pos = min(widget.width() * idx, screen_width - widget.width())
                y_pos = (widget.height() // 2) * (idx * widget.width() // screen_width)
                widget.move(x_pos,y_pos)
                self.camera_widgets[camID] = widget
                cam_item.setBackground(QtGui.QColorConstants.Green)

            elif cam_widget.paused: # Toggle paused widget to resume
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
                cam_item.setBackground(QtGui.QColorConstants.LightGray)

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