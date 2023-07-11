import sys
import time
from pyqtconfig import ConfigManager

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from interface.design.Ui_MainWindow import Ui_MainWindow
from interface.camera_widget import CameraWidget


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, camera_models = [], plugins = []):
        super().__init__()
        self.setupUi(self)

        # Set geometry relative to screen
        self.screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (self.screen.width() - self.width()) // 2
        y_pos = 2 * (self.screen.height() - self.height()) // 3
        self.move(x_pos, y_pos)

        # Create ID look-ups for cameras, widgets, and configs
        self.cameras = {}
        self.camera_widgets = {}
        self.camera_models = camera_models
        self.populate_available_cameras()

        self.camera_configs = {id : ConfigManager() for id in self.cameras.keys()}
        self.populate_camera_properties()
        self.populate_camera_stats()

        # Create name look-ups for plugin classes and configs
        self.plugins = {p.__name__ : p for p in plugins}
        self.populate_plugin_list()

        self.plugin_configs = {p.__name__ : ConfigManager() for p in plugins}
        self.populate_plugin_settings()
        self.populate_plugin_pipeline()
        
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
        self.update_timer.start(250)


    def update_camera_stats(self):
        for row, camera in enumerate(self.cameras.values()):
            self.cam_stats.item(row, 0).setText(camera.getName())
            self.cam_stats.item(row, 1).setText(str(camera.frames_acquired))
            if hasattr(camera, "frames_dropped"):
                self.cam_stats.item(row, 2).setText(str(camera.frames_dropped))
            else:
                self.cam_stats.item(row, 2).setText("N/A")

            # widget = self.camera_widgets[name]
            # if widget is not None:
            #     for col, plugin in enumerate(widget.plugins):
            #         if row == 0: # Only set header once
            #             header_item = QtWidgets.QTableWidgetItem(type(plugin).__name__ + " Queue")
            #             self.cam_stats.setHorizontalHeaderItem(3+col, header_item)

            #         self.cam_stats.setItem(row, 3+col, QtWidgets.QTableWidgetItem(str(plugin.in_queue.qsize())))
        
        self.cam_stats.resizeColumnsToContents()
    
    # def update_plugin_stats(self):
    #     pass

    def populate_available_cameras(self):
        self.cam_list.clear()
        self.cam_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.cam_list.itemChanged.connect(self.populate_plugin_pipeline)
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
                if cam.getName() not in self.cameras.keys():
                    self.cameras[cam.getName()] = cam
                    self.camera_widgets[cam.getName()] = None
    

    def populate_camera_properties(self):
        for camID, config in self.camera_configs.items():
            tab = QtWidgets.QLabel('camID')
            cls = self.cameras[camID].__class__
            tab = QtWidgets.QWidget()
            if hasattr(cls, "DEFAULT_PROPS"):
                config.set_defaults(cls.DEFAULT_PROPS)
                for key, value in cls.DEFAULT_PROPS.items():
                    if isinstance(value, bool):
                        widget = QtWidgets.QCheckBox()
                    elif isinstance(value, str):
                        widget = QtWidgets.QLineEdit()
                    elif isinstance(value, int):
                        widget = QtWidgets.QSpinBox()
                    elif isinstance(value, list):
                        widget = QtWidgets.QComboBox()
                        widget.addItems(value)
                        config.set_default(key, value[0])

                    config.add_handler(key, widget)
            
            layout = make_config_layout(config)
            # layout.setSpacing(0)
            # layout.addStretch()
            layout.insertStretch(1, 1)
            tab.setLayout(layout)
            self.cam_props.addTab(tab, str(camID))


    def populate_camera_stats(self):
        self.cam_stats.setRowCount(len(self.cameras))
        for row, (name, camera)  in enumerate(self.cameras.items()):
            self.cam_stats.setItem(row, 0, QtWidgets.QTableWidgetItem(name))
            self.cam_stats.setItem(row, 1, QtWidgets.QTableWidgetItem(str(camera.frames_acquired)))

            if hasattr(camera, "frames_dropped"):
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem(str(camera.frames_dropped)))
            else:
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem("N/A"))


    def populate_plugin_list(self):
        self.plugin_list.clear()
        self.plugin_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.plugin_list.itemChanged.connect(self.populate_plugin_pipeline)
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

    def populate_plugin_settings(self):
        for name, config in self.plugin_configs.items():
            cls = self.plugins[name]
            tab = QtWidgets.QWidget()
            if hasattr(cls, "DEFAULT_CONFIG"):
                config.set_defaults(cls.DEFAULT_CONFIG)
                for key, value in cls.DEFAULT_CONFIG.items():
                    if isinstance(value, bool):
                        widget = QtWidgets.QCheckBox()
                    elif isinstance(value, str):
                        widget = QtWidgets.QLineEdit()
                    elif isinstance(value, int):
                        widget = QtWidgets.QSpinBox()
                    elif isinstance(value, list):
                        widget = QtWidgets.QComboBox()
                        widget.addItems(value)
                        config.set_default(key, value[0])

                    config.add_handler(key, widget)
            
            layout = make_config_layout(config)
            layout.insertStretch(1, 5)
            tab.setLayout(layout)
            self.plugin_settings.addTab(tab, name)
    

    def populate_plugin_pipeline(self):
        self.plugin_pipeline.clear()
        try: self.plugin_pipeline.disconnect() # Disconnect all signal-slots
        except Exception: pass

        self.plugin_pipeline.setRowCount(len(self.camera_widgets))
        self.plugin_pipeline.setVerticalHeaderLabels(self.camera_widgets.keys())

        self.plugin_pipeline.setColumnCount(len(self.plugins.keys()))
        self.plugin_pipeline.setHorizontalHeaderLabels(self.plugins.keys())

        checked_camera_names = [c.text() for c in get_checked_items(self.cam_list)]
        checked_plugin_names = [p.text() for p in get_checked_items(self.plugin_list)]

        for row, (camID, widget) in enumerate(self.camera_widgets.items()):
            for col, plugin_name in enumerate(self.plugins.keys()):
                item = self.plugin_pipeline.item(row, col)
                if item is None:
                    item = QtWidgets.QTableWidgetItem()
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.plugin_pipeline.setItem(row, col, item)

                if widget is not None: # Active
                    plugin_active = None
                    for plugin in widget.plugins: # Find plugin by name
                        if isinstance(plugin, self.plugins[plugin_name]):
                            plugin_active = plugin.active
                            break

                    if not widget.active:
                         item.setText("Paused")
                         item.setBackground(QtGui.QColorConstants.LightGray)
                    elif plugin_active == None:
                        item.setText("Inactive")
                        item.setBackground(QtGui.QColorConstants.DarkGray)
                    elif plugin_active:
                        item.setText("Active")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Checked)
                        item.setBackground(QtGui.QColorConstants.Green)
                    else:
                        item.setText("Paused")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        item.setBackground(QtGui.QColorConstants.LightGray)
                elif camID in checked_camera_names: # Enabled
                    if plugin_name in checked_plugin_names:
                        item.setText("Enabled")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setText("Disabled")
                        item.setBackground(QtGui.QColorConstants.DarkGray)
                else:
                    item.setText("Disabled")
                    item.setBackground(QtGui.QColorConstants.DarkGray)
        
        self.plugin_pipeline.itemChanged.connect(self.toggle_camera_plugin)
        self.plugin_pipeline.resizeColumnsToContents()


    def toggle_camera_plugin(self, item):
        camID = self.plugin_pipeline.verticalHeaderItem(item.row()).text()
        plugin_name = self.plugin_pipeline.horizontalHeaderItem(item.column()).text()

        if item.checkState() == Qt.CheckState.Checked:
            if item.text() == "Paused":
                item.setText("Active")
                item.setBackground(QtGui.QColorConstants.Green)
                widget = self.camera_widgets[camID]
                for plugin in widget.plugins: # Find plugin by name
                    if isinstance(plugin, self.plugins[plugin_name]):
                        plugin.active = True
                        break
            elif item.text() == "Disabled":
                item.setText("Enabled") 
                item.setBackground(QtGui.QColorConstants.White) # Reset to default color

        elif item.checkState() == Qt.CheckState.Unchecked:
            if item.text() == "Active":
                item.setText("Paused")
                item.setBackground(QtGui.QColorConstants.LightGray)
                widget = self.camera_widgets[camID]
                for plugin in widget.plugins: # Find plugin by name
                    if isinstance(plugin, self.plugins[plugin_name]):
                        plugin.active = False
                        break
            elif item.text() == "Enabled":
                item.setText("Disabled")
                item.setBackground(QtGui.QColorConstants.DarkGray)


    def start_camera_widgets(self):        
        screen_width = self.screen.width()
        for row in range(self.plugin_pipeline.rowCount()):
            camID = self.plugin_pipeline.verticalHeaderItem(row).text()
            widget = self.camera_widgets[camID]

            if widget is None: # Create new widget
                enabled_plugins = []
                for col in range(self.plugin_pipeline.columnCount()):
                    plugin_name = self.plugin_pipeline.horizontalHeaderItem(col).text()
                    item = self.plugin_pipeline.item(row, col)
                    if item.text() == "Enabled":
                        enabled_plugins.append(self.plugins[plugin_name])
                if len(enabled_plugins) == 0:
                    print("At least one plugin must be selected")
                    break

                widget = CameraWidget(camera=self.cameras[camID], plugins=enabled_plugins)
                x_pos = min(widget.width() * row, screen_width - widget.width())
                y_pos = (widget.height() // 2) * (row * widget.width() // screen_width)
                widget.move(x_pos,y_pos)
                self.camera_widgets[camID] = widget
                self.cam_list.item(row).setBackground(QtGui.QColorConstants.Green)
                self.camera_widgets[camID].show()
            elif not widget.active: # Toggle paused widget to resume
                widget.active = True
                widget.setBackground(QtGui.QColorConstants.Green)
                self.camera_widgets[camID].show()

        self.populate_plugin_pipeline()


    def pause_camera_widgets(self):
        for cam_item in get_checked_items(self.cam_list):
            camID = cam_item.text()
            cam_widget = self.camera_widgets[camID]
            if cam_widget is not None:
                cam_widget.active = False
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


def make_config_layout(config, cols=2):
    """
    Generate a layout based on the input ConfigManager. The layout consists of a user specified number of columns of
    QFormLayout. In each row of the QFormLayout, the label is the config dict key, and the field is the config handler
    for that key.

    :param config: ConfigManager
    :param cols: Number of columns to use
    :return: QHBoxLayout
    """
    h_layout = QtWidgets.QHBoxLayout()
    forms = [QtWidgets.QFormLayout() for _ in range(cols)]
    for form in forms:
        h_layout.addLayout(form, 3)

    num_items = len(config.get_visible_keys())
    for i, key in enumerate(config.get_visible_keys()):
        # Find which column to put the setting in. Columns are filled equally, with remainder to the left. Each column
        # is filled before proceeding to the next.
        f_index = i % cols

        # Get the handler widget for the key
        if key in config.handlers:
            # If we've already defined a handler, use that
            input_widget = config.handlers[key]
        else:
            # Otherwise, try to add a handler. If it fails, skip this row
            config.add_handler(key)
            if key not in config.handlers:
                continue
            else:
                input_widget = config.handlers[key]

        label = QtWidgets.QLabel(key)
        forms[f_index].addRow(label, input_widget)

    return h_layout