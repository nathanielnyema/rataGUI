import os
import json
from datetime import datetime

from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QDialogButtonBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from rataGUI.interface.design.Ui_StartMenu import Ui_StartMenu
from rataGUI import config_path, launch_config, rataGUI_icon

import logging
logger = logging.getLogger(__name__)


class StartMenu(QDialog, Ui_StartMenu):

    def __init__(self, camera_modules = [], plugin_modules = [], trigger_modules = []):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(rataGUI_icon))

        self.camera_models = {}
        for cls in camera_modules:
            self.camera_models[cls.__name__] = cls
            item = QListWidgetItem(cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.camera_modules.addItem(item)
        self.camera_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked)
        )

        self.plugins = {}
        for cls in plugin_modules:
            self.plugins[cls.__name__] = cls
            item = QListWidgetItem(cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.plugin_modules.addItem(item)
        self.plugin_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked)
        )

        self.trigger_types = {}
        for cls in trigger_modules:
            self.trigger_types[cls.__name__] = cls
            item = QListWidgetItem(cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.trigger_modules.addItem(item)
        self.trigger_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked)
        )

        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.save_settings)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.load_settings)
        self.closeEvent = self.load_settings
        

    def load_settings(self, event=None):
        save_dir = self.save_directory.text()
        if len(save_dir) == 0:
            save_dir = os.path.abspath("rataGUI_" + datetime.now().strftime('%Y-%m-%d'))
            logger.warning(f"No save directory specified ... defaulting to {save_dir}")
        else:
            save_dir = os.path.abspath(os.path.normpath(save_dir))

        try:
            os.makedirs(save_dir, exist_ok=True)
            logger.info(f"Saving all session data to {save_dir}")
        except Exception as err:
            logger.exception(err)
            logger.error(f"Invalid save directory specified")
            raise

        launch_config["Enabled Camera Modules"] = [module_name(self.camera_models[name]) for name in get_checked_names(self.camera_modules)]
        launch_config["Enabled Plugin Modules"] = [module_name(self.plugins[name]) for name in get_checked_names(self.plugin_modules)]
        launch_config["Enabled Trigger Modules"] = [module_name(self.trigger_types[name]) for name in get_checked_names(self.trigger_modules)]
        launch_config["Save Directory"] = save_dir
        launch_config["FFMPEG Path"] = self.ffmpeg_path.text()

    
    def save_settings(self):
        logger.info("Launch settings saved. Run \"rataGUI --start-menu\" to reconfigure.")
        self.load_settings()
        with open(config_path, 'w') as file:
            json.dump(launch_config, file, indent=2)        


def get_checked_names(check_list: QListWidget) -> list:
    checked = []
    for idx in range(check_list.count()):
        item = check_list.item(idx)
        if item.checkState() == Qt.CheckState.Checked:
            checked.append(item.text())
    return checked


def module_name(cls):
    return cls.__module__.split('.')[-1]