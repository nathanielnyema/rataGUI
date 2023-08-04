import os
# import sys
import time
import json
import asyncio
from collections import OrderedDict

from pyqtconfig import ConfigManager
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QTimer

from interface.design.Ui_MainWindow import Ui_MainWindow
from interface.camera_widget import CameraWidget
from config import restore_session, save_directory

import psutil

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, camera_models = [], plugins = [], trigger_types = [], dark_mode=True):
        super().__init__()
        self.setupUi(self)

        # Set geometry relative to screen
        self.screen = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        x_pos = (self.screen.width() - self.width()) // 2
        y_pos = 3 * (self.screen.height() - self.height()) // 4
        self.move(x_pos, y_pos)

        # Configure color scheme
        if dark_mode:
            self.active_color = QtGui.QColorConstants.DarkMagenta
            self.paused_color = QtGui.QColorConstants.DarkGray
            self.inactive_color = QtGui.QColorConstants.Black
        else:
            self.active_color = QtGui.QColorConstants.Green
            self.paused_color = QtGui.QColorConstants.LightGray
            self.inactive_color = QtGui.QColorConstants.DarkGray

        # Create mappings from camID to camera, widget, config and model
        self.cameras = {}
        self.camera_widgets = {}
        self.camera_configs = {}
        self.camera_names = OrderedDict() # map camID to display name
        self.camera_models = {c.__name__ : c for c in camera_models}
        self.populate_camera_list()
        self.populate_camera_properties()
        self.populate_camera_stats()

        # Create mappings from name to plugin class and configs
        self.plugins = {p.__name__ : p for p in plugins}
        self.plugin_configs = {}
        self.populate_plugin_list()
        self.populate_plugin_settings()
        self.populate_plugin_pipeline()

        self.triggers = {}          # deviceID -> trigger object
        self.trigger_tabs = {}      # trigger type -> tab widget
        self.trigger_configs = {}   # enabled trigger -> config manager
        self.trigger_types = {t.__name__ : t for t in trigger_types}
        self.populate_camera_triggers()

        if restore_session: self.restore_session() # Load config from session 
        
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

        self.logging_timer = QTimer()
        self.logging_timer.timeout.connect(self.log_computer_stats)
        self.logging_timer.start(30000)

    def log_computer_stats(self):
        process = psutil.Process(os.getpid())
        cpu = process.cpu_percent(interval=1)
        mem = process.memory_info().rss / float(2 ** 20)
        with open("log.txt", "a") as f:
            print("CPU (%): "+str(cpu)+"\tRAM: "+str(mem), file=f)

    def update_camera_stats(self): # Save stats?
        for row, camera in enumerate(self.cameras.values()):
            # self.cam_stats.item(row, 0).setText(self.camera_names[camera.getName()])
            self.cam_stats.item(row, 0).setText(camera.getName())
            self.cam_stats.item(row, 1).setText(str(camera.frames_acquired))
            if hasattr(camera, "frames_dropped"):
                self.cam_stats.item(row, 2).setText(str(camera.frames_dropped))
            else:
                self.cam_stats.item(row, 2).setText("N/A")

            if hasattr(camera, "buffer_size"):
                self.cam_stats.item(row, 3).setText(str(camera.buffer_size))
            else:
                self.cam_stats.item(row, 3).setText("N/A")
    
    # def update_plugin_stats(self):
    #     pass

    def rename_camera(self, item):
        new_name = item.text()
        camID, old_name = self.camera_names.popitem()

        if new_name not in self.camera_names.keys() or old_name == new_name:
            if new_name in self.camera_names.values():
                print("Warning: Display name is already used by another camera.")
            self.camera_names[camID] = new_name
            self.cameras[camID].display_name = new_name
            self.populate_camera_properties()
        else:
            self.camera_names[camID] = old_name
            self.camera_names.move_to_end(new_name)

        self.populate_plugin_pipeline()

    def populate_camera_list(self):
        self.cam_list.clear()
        self.cam_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.cam_list.itemChanged["QListWidgetItem*"].connect(self.rename_camera)
        self.cam_list.itemDoubleClicked["QListWidgetItem*"].connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )
        self.cam_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.DoubleClicked)

        for camera_cls in self.camera_models.values():
            cam_list = camera_cls.getAvailableCameras()
            for cam in cam_list:
                camID = cam.getName()
                # Initialize all camera-specific items
                if camID not in self.cameras.keys():
                    self.cameras[camID] = cam
                    self.camera_widgets[camID] = None
                    self.camera_configs[camID] = ConfigManager()
                    self.camera_names[camID] = str(camID)
                
                item = QtWidgets.QListWidgetItem(self.camera_names[camID])
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.cam_list.addItem(item)

        
        # Ensure consistent ordering throughout interface
        self.cameras = dict(sorted(self.cameras.items()))
        self.camera_widgets = dict(sorted(self.camera_widgets.items()))
    

    def populate_camera_properties(self):
        self.cam_props.clear() # TODO
        for camID, config in self.camera_configs.items():
            cls = self.cameras[camID].__class__
            tab = QtWidgets.QWidget()
            if hasattr(cls, "DEFAULT_PROPS"):
                config.set_defaults(cls.DEFAULT_PROPS)
                for key, setting in cls.DEFAULT_PROPS.items():
                    add_config_handler(config, key, setting)
            
            layout = make_config_layout(config)
            tab.setLayout(layout)
            self.cam_props.addTab(tab, self.camera_names[camID])


    def populate_camera_stats(self):
        self.cam_stats.setRowCount(len(self.cameras))
        for row, camera in enumerate(self.cameras.values()):
            name_item = QtWidgets.QTableWidgetItem(camera.getName())
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cam_stats.setItem(row, 0, name_item)
            self.cam_stats.setItem(row, 1, QtWidgets.QTableWidgetItem(str(camera.frames_acquired)))

            if hasattr(camera, "frames_dropped"):
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem(str(camera.frames_dropped)))
            else:
                self.cam_stats.setItem(row, 2, QtWidgets.QTableWidgetItem("N/A"))

            if hasattr(camera, "buffer_size"):
                self.cam_stats.setItem(row, 3, QtWidgets.QTableWidgetItem(str(camera.buffer_size)))
            else:
                self.cam_stats.setItem(row, 3, QtWidgets.QTableWidgetItem("N/A"))

        self.cam_stats.resizeColumnsToContents()


    def populate_plugin_list(self):
        self.plugin_list.clear()
        self.plugin_list.setItemAlignment(Qt.AlignmentFlag.AlignTop)
        self.plugin_list.itemChanged.connect(self.populate_plugin_pipeline)
        self.plugin_list.model().rowsMoved.connect(self.populate_plugin_pipeline)
        self.plugin_list.itemDoubleClicked["QListWidgetItem*"].connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for name in self.plugins.keys():
            item = QtWidgets.QListWidgetItem(name)
            # item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.plugin_list.addItem(item)
            self.plugin_configs[name] = ConfigManager()


    def populate_plugin_settings(self):
        self.plugin_settings.clear()
        for plugin_name, config in self.plugin_configs.items():
            cls = self.plugins[plugin_name]
            tab = QtWidgets.QWidget()
            if hasattr(cls, "DEFAULT_CONFIG"):
                config.set_defaults(cls.DEFAULT_CONFIG)
                for key, setting in cls.DEFAULT_CONFIG.items():
                    add_config_handler(config, key, setting)

                if cls.__name__ == "MetadataWriter": # add missing metadata to UI
                    for camera in self.cameras.values():
                        metadata = camera.getMetadata()
                        settings =  config.get_visible_keys()
                        for name in metadata.keys():
                            key = 'Overlay ' + name
                            if key not in settings:
                                add_config_handler(config, key, value=False)
            
            layout = make_config_layout(config)
            tab.setLayout(layout)
            self.plugin_settings.addTab(tab, plugin_name)


    def populate_plugin_pipeline(self):
        self.plugin_pipeline.clear()
        try: self.plugin_pipeline.disconnect() # Disconnect all signal-slots
        except Exception: pass

        self.plugin_pipeline.setRowCount(len(self.camera_widgets))
        self.plugin_pipeline.setColumnCount(self.plugin_list.count())
        column_labels = []

        # TODO: Use self.cam_list directly if order can change
        checked_camera_names = [c.text() for c in get_checked_items(self.cam_list)]

        for row, (camID, widget) in enumerate(self.camera_widgets.items()):
            for col in range(self.plugin_list.count()):
                plugin_item = self.plugin_list.item(col)
                plugin_name = plugin_item.text()
                if row == 0: # Add column label once
                    column_labels.append(plugin_name)

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
                         item.setBackground(self.paused_color)
                    elif plugin_active == None:
                        item.setText("Inactive")
                        item.setBackground(self.inactive_color)
                    elif plugin_active:
                        item.setText("Active")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Checked)
                        item.setBackground(self.active_color)
                    else:
                        item.setText("Paused")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        item.setBackground(self.paused_color)
                elif self.camera_names[camID] in checked_camera_names: # Camera is enabled
                    if plugin_item.checkState() == Qt.CheckState.Checked: # Plugin is enabled
                        item.setText("Enabled")
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setText("")
                        item.setBackground(self.inactive_color)
                else:
                    item.setText("")
                    item.setData(Qt.ItemDataRole.BackgroundRole, None) # Reset to default color

        cam_names = [self.camera_names[camID] for camID in self.camera_widgets.keys()]
        self.plugin_pipeline.setVerticalHeaderLabels(cam_names)
        self.plugin_pipeline.setHorizontalHeaderLabels(column_labels)
        
        self.plugin_pipeline.itemChanged.connect(self.toggle_camera_plugin)
        self.plugin_pipeline.resizeColumnsToContents()


    def toggle_camera_plugin(self, item):
        camID = self.plugin_pipeline.verticalHeaderItem(item.row()).text()
        plugin_name = self.plugin_pipeline.horizontalHeaderItem(item.column()).text()

        if item.checkState() == Qt.CheckState.Checked:
            if item.text() == "Paused":
                item.setText("Active")
                item.setBackground(self.active_color)
                widget = self.camera_widgets[camID]
                for plugin in widget.plugins: # Find plugin by name
                    if isinstance(plugin, self.plugins[plugin_name]):
                        plugin.active = True
                        break
            elif item.text() == "Disabled":
                item.setText("Enabled")
                item.setData(Qt.ItemDataRole.BackgroundRole, None) # Reset to default color

        elif item.checkState() == Qt.CheckState.Unchecked:
            if item.text() == "Active":
                item.setText("Paused")
                item.setBackground(self.paused_color)
                widget = self.camera_widgets[camID]
                for plugin in widget.plugins: # Find plugin by name
                    if isinstance(plugin, self.plugins[plugin_name]):
                        plugin.active = False
                        break
            elif item.text() == "Enabled":
                item.setText("Disabled")
                item.setBackground(self.inactive_color)


    def populate_camera_triggers(self):
        self.cam_triggers.clear()
        for trigger_cls in self.trigger_types.values():
            tab = QtWidgets.QWidget()
            self.cam_triggers.addTab(tab, trigger_cls.__name__)
            layout = QtWidgets.QVBoxLayout()
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)

            options = QtWidgets.QComboBox()
            options.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            device_list = trigger_cls.getAvailableDevices()
            for trigger in device_list:
                deviceID = str(trigger.deviceID)
                if deviceID not in self.triggers.keys():
                    self.triggers[deviceID] = trigger
                    options.addItem(deviceID)

            options.model().sort(0)
            options_layout = QtWidgets.QHBoxLayout()
            options_layout.addWidget(options, stretch=2)
            add_btn = QtWidgets.QPushButton("Add Trigger")
            add_btn.clicked.connect(lambda state, x=options: self.add_trigger_config(x))
            options_layout.addWidget(add_btn, stretch=1)

            layout.addLayout(options_layout)
            tab.setLayout(layout)
            self.trigger_tabs[trigger_cls.__name__] = tab

    def add_trigger_config(self, options):
        deviceID = options.currentText()
        config = ConfigManager()
        trigger_cls = type(self.triggers[deviceID])
        if hasattr(trigger_cls, "DEFAULT_CONFIG"):
            config.set_defaults(trigger_cls.DEFAULT_CONFIG)
            for key, setting in trigger_cls.DEFAULT_CONFIG.items():
                add_config_handler(config, key, setting)
        self.trigger_configs[deviceID] = config

        config_layout = make_config_layout(config)
        delete_btn = QtWidgets.QToolButton()
        delete_btn.setFixedSize(15,15)
        delete_btn.setText('X')
        config_layout.addWidget(delete_btn)

        config_box = QtWidgets.QGroupBox(deviceID)
        config_box.setLayout(config_layout)
        config_box.setCheckable(True)
        layout = self.trigger_tabs[trigger_cls.__name__].layout()
        layout.insertWidget(layout.count()-1, config_box)

        delete_btn.clicked.connect(lambda: self.remove_trigger_config(config_box, options))
        options.removeItem(options.currentIndex())

    def remove_trigger_config(self, config_box, options):
        config_box.setParent(None)
        config_box.deleteLater()
        deviceID = config_box.title()
        self.trigger_configs.pop(deviceID)

        for i in range(options.count()):
            if options.itemText(i) > deviceID:
                options.insertItem(i, deviceID)
                break


    def start_camera_widgets(self):
        screen_width = self.screen.width()
        for row in range(self.plugin_pipeline.rowCount()):
            cam_name = self.plugin_pipeline.verticalHeaderItem(row).text()
            camID = list(self.camera_names.keys())[list(self.camera_names.values()).index(cam_name)] # cam_name -> camID
            widget = self.camera_widgets[camID]
            if widget is None: # Create new widget 
                enabled_plugins = []
                for col in range(self.plugin_pipeline.columnCount()):
                    plugin_name = self.plugin_pipeline.horizontalHeaderItem(col).text()
                    item = self.plugin_pipeline.item(row, col)
                    if item.text() == "Enabled":
                        enabled_plugins.append((self.plugins[plugin_name], self.plugin_configs[plugin_name]))
                if len(enabled_plugins) == 0:
                    # print("At least one plugin must be selected")
                    continue

                # Initialize all enabled triggers
                enabled_triggers = []
                for enabled_name, config in self.trigger_configs.items():
                    trigger = self.triggers[enabled_name]
                    if not trigger.initialized:
                        trigger.initialize(config)
                    enabled_triggers.append(trigger)
                
                config = self.camera_configs[camID].as_dict()
                widget = CameraWidget(camera=self.cameras[camID], cam_config=config, plugins=enabled_plugins, triggers=enabled_triggers)
                x_pos = min(widget.width() * row, screen_width - widget.width())
                y_pos = (widget.height() // 2) * (row * widget.width() // screen_width)
                widget.move(x_pos,y_pos)
                self.camera_widgets[camID] = widget
                self.cam_list.item(row).setBackground(self.active_color)
                self.camera_widgets[camID].show()
            elif not widget.active: # Toggle paused widget to resume
                widget.active = True
                self.cam_list.item(row).setBackground(self.active_color)
                self.camera_widgets[camID].show()
        # Update camera pipeline
        self.populate_plugin_pipeline()


    def pause_camera_widgets(self):
        for cam_item in get_checked_items(self.cam_list):
            cam_name = cam_item.text()
            camID = list(self.camera_names.keys())[list(self.camera_names.values()).index(cam_name)] # cam_name -> camID
            cam_widget = self.camera_widgets[camID]
            if cam_widget is not None:
                cam_widget.active = False
                cam_item.setBackground(self.paused_color)


    def stop_camera_widgets(self):
        for cam_item in get_checked_items(self.cam_list):
            cam_name = cam_item.text()
            camID = list(self.camera_names.keys())[list(self.camera_names.values()).index(cam_name)] # cam_name -> camID
            cam_widget = self.camera_widgets[camID]
            if cam_widget is not None:
                self.camera_widgets[camID] = None
                cam_widget.close_widget()
                cam_item.setData(Qt.ItemDataRole.BackgroundRole, None) # Reset to default color

        # Stop triggers
        for trigger in self.triggers.values():
            if trigger.initialized:
                trigger.stop()


    def save_session(self):
        save_dir = os.path.abspath(save_directory)
        os.makedirs(save_dir, exist_ok=True)
        cam_settings = {}
        for camID, config in self.camera_configs.items():
            cam_settings[camID] = config.as_dict()
        with open(os.path.join(save_dir, "camera_settings.json"), 'w') as file:
            json.dump(cam_settings, file, indent=2)

        plugin_settings = {}
        for name, config in self.plugin_configs.items():
            plugin_settings[name] = config.as_dict()
        with open(os.path.join(save_dir, "plugin_settings.json"), 'w') as file:
            json.dump(plugin_settings, file, indent=2)

        trigger_settings = {}
        for name, config in self.trigger_configs.items():
            trigger_settings[name] = config.as_dict()
        with open(os.path.join(save_dir, "trigger_settings.json"), 'w') as file:
            json.dump(trigger_settings, file, indent=2)

        ui_settings = {}
        ui_settings["camera_names"] = self.camera_names
        ui_settings["checked_cameras"] = [c.text() for c in get_checked_items(self.cam_list)]

        plugin_states = {}
        for idx in range(self.plugin_list.count()):
            item = self.plugin_list.item(idx)
            plugin_states[item.text()] = item.checkState() == Qt.CheckState.Checked
        ui_settings["plugin_states"] = plugin_states

        # ui_settings["active_camera_tab"] = self.camAttributes.currentWidget().objectName()
        # ui_settings["active_plugin_tab"] = self.plugin_settings.currentWidget().objectName()

        ui_settings["window_width"] = self.size().width()
        ui_settings["window_height"] = self.size().height()
        ui_settings["window_x"] = self.pos().x()
        ui_settings["window_y"] = self.pos().y()
        with open(os.path.join(save_dir, "interface_settings.json"), 'w') as file:
            json.dump(ui_settings, file, indent=2)

    def restore_session(self):
        save_dir = os.path.abspath(save_directory)
        cam_config_path = os.path.join(save_dir, "camera_settings.json")
        if os.path.exists(cam_config_path): 
            with open(cam_config_path, 'r') as file:
                saved_configs = json.load(file)
            for camID, config in self.camera_configs.items():
                if camID in saved_configs.keys():
                    config.set_many(saved_configs[camID])
                    # TODO: Catch error when saved setting is not in config
        else:
            print("No saved camera settings ... using defaults")

        plugin_config_path = os.path.join(save_dir, "plugin_settings.json")
        if os.path.exists(plugin_config_path): 
            with open(plugin_config_path, 'r') as file:
                saved_configs = json.load(file)
            for name, config in self.plugin_configs.items():
                if name in saved_configs.keys():
                    config.set_many(saved_configs[name])
                    # TODO: Catch error when saved setting is not in config
        else:
            print("No saved plugin settings ... using defaults")

        trigger_config_path = os.path.join(save_dir, "trigger_settings.json")
        if os.path.exists(trigger_config_path): 
            with open(trigger_config_path, 'r') as file:
                saved_configs = json.load(file)
            for deviceID, trigger in self.triggers.items():
                if deviceID in saved_configs.keys():
                    # Add trigger by "pressing" interface button
                    trigger_type = type(trigger).__name__
                    layout = self.trigger_tabs[trigger_type].layout()
                    options = layout.itemAt(layout.count()-1).itemAt(0).widget()
                    options.setCurrentText(deviceID)
                    self.add_trigger_config(options)
        else:
            print("No saved trigger settings ... using defaults")

        ui_config_path = os.path.join(save_dir, "interface_settings.json")
        if os.path.exists(ui_config_path): 
            with open(ui_config_path, 'r') as file:
                saved_configs = json.load(file)

            # Restore camera list to saved state
            for idx in range(self.cam_list.count()):
                item = self.cam_list.item(idx)
                camID = item.text()
                # Rename cameras to saved display names
                if camID in saved_configs["camera_names"]:
                    item.setText(saved_configs["camera_names"][camID])

                if item.text() in saved_configs["checked_cameras"]:
                    item.setCheckState(Qt.CheckState.Checked)

            # Repopulate list with saved plugin state and order
            self.plugin_list.clear()
            for name, checked in saved_configs["plugin_states"].items():
                if name in self.plugins:
                    item = QtWidgets.QListWidgetItem(name)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    if checked:
                        item.setCheckState(Qt.CheckState.Checked)
                    self.plugin_list.addItem(item)

            # Append any new plugins to the end
            new_plugins = list(set(self.plugins) - set(saved_configs["plugin_states"]))
            for name in new_plugins:
                item = QtWidgets.QListWidgetItem(name)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.plugin_list.addItem(item)
            
            self.populate_plugin_pipeline()

            # active_camera_tab = self.camAttributes.findChild(QtWidgets.QWidget, saved_configs["active_camera_tab"])
            # self.camAttributes.setCurrentIndex(self.camAttributes.indexOf(active_camera_tab))


            # active_plugin_tab = self.plugin_settings.findChild(QtWidgets.QWidget, saved_configs["active_plugin_tab"])
            # self.plugin_settings.setCurrentWidget(active_plugin_tab)

            self.resize(saved_configs["window_width"], saved_configs["window_height"])
            self.move(saved_configs["window_x"], saved_configs["window_y"])
        else:
            print("No saved interface settings ... using defaults")
        

    def closeEvent(self, event):
        for cam_widget in self.camera_widgets.values():
            if cam_widget is not None:
                cam_widget.close_widget()

        # Save session configuration as json files
        self.save_session()

        # Wait for threads to stop TODO: More sophisticated way to wait for threads to stop
        time.sleep(0.2)

        # Release camera-specific resources
        for cam_type in self.camera_models.values():
            cam_type.releaseResources()

        QtWidgets.QMainWindow.closeEvent(self, event) # let the window close


def get_checked_items(check_list: QtWidgets.QListWidget) -> list:
    checked = []
    for idx in range(check_list.count()):
        item = check_list.item(idx)
        if item.checkState() == Qt.CheckState.Checked:
            checked.append(item)
    return checked


def add_config_handler(config, key, value):
    try:
        # if isinstance(key, list): # Mutually exclusive options
        #     key = tuple(key)
        #     value = value[0]

        mapper = (lambda x: x, lambda x: x)
        if isinstance(value, bool):
            widget = QtWidgets.QCheckBox()
        elif isinstance(value, str):
            widget = QtWidgets.QLineEdit()
        elif isinstance(value, int):
            widget = QtWidgets.QSpinBox()
            widget.setMinimum(-1)
        elif isinstance(value, float):
            widget = QtWidgets.QDoubleSpinBox()
            widget.setSingleStep(0.1)
        elif isinstance(value, tuple):
            widget = QtWidgets.QSpinBox()
            if len(value) == 3:
                widget.setRange(value[1], value[2])
            config.set_default(key, value[0])
        elif isinstance(value, list):
            widget = QtWidgets.QComboBox()
            widget.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            widget.addItems(value)
            config.set_default(key, value[0]) # Default to first value
        elif isinstance(value, dict):
            widget = QtWidgets.QComboBox()
            widget.view().setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            options = list(value.keys())
            widget.addItems(options)
            config.set_default(key, value[options[0]]) # Default to first value
            mapper = value

        config.add_handler(key, widget, mapper) 
    except Exception as err:
        print('ERROR--GUI: %s' % err)
        print("Failed to create setting handler. Each setting must correspond to a valid set of values")


def make_config_layout(config, cols=2):
    """
    Generate a QHBoxLayout based on the input ConfigManager where each column is a QFormLayout
    For each row, the label is the config dict key, and the field is the config handler for that key.

    :param config: ConfigManager
    :param cols: Number of columns to use
    :return: QHBoxLayout
    """
    layout = QtWidgets.QHBoxLayout()

    # if len(config.get_visible_keys()) < 4:
    #     cols = 1

    forms = [QtWidgets.QFormLayout() for _ in range(cols)]
    for form in forms:
        form.setContentsMargins(5,0,5,0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addLayout(form, stretch=5)

    line_edits = []
    count = 0
    for key in config.get_visible_keys():
        f_index = count % cols
        handler = config.handlers[key]
        label = QtWidgets.QLabel(key)

        if isinstance(handler, QtWidgets.QLineEdit):
            line_edits.append((label, handler))
        else:
            forms[f_index].addRow(label, handler)
            count += 1

    if len(line_edits) > 0:
        line_form = QtWidgets.QFormLayout()
        line_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for label, handler in line_edits:
            line_form.addRow(label, handler)
        
        new_layout = QtWidgets.QVBoxLayout()
        new_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        new_layout.addLayout(line_form)
        new_layout.addLayout(layout)
        return new_layout

    return layout
