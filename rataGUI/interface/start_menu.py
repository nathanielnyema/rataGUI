import os
import json
from datetime import datetime

from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QDialogButtonBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt # QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from rataGUI.interface.design.Ui_StartMenu import Ui_StartMenu

import logging
logger = logging.getLogger(__name__)


class StartMenu(QDialog, Ui_StartMenu):

    def __init__(self, camera_models = [], plugins = [], trigger_types = []):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon('rataGUI/interface/design/ratagui-icon.png'))

        for camera_cls in camera_models:
            item = QListWidgetItem(camera_cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.camera_modules.addItem(item)
        self.camera_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for plugin_cls in plugins:
            item = QListWidgetItem(plugin_cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.plugin_modules.addItem(item)
        self.plugin_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        for trigger_cls in trigger_types:
            item = QListWidgetItem(trigger_cls.__name__)
            item.setCheckState(Qt.CheckState.Checked)
            self.trigger_modules.addItem(item)
        self.trigger_modules.itemDoubleClicked.connect(
            lambda item: item.setCheckState(Qt.CheckState.Checked 
                if item.checkState() == Qt.CheckState.Unchecked else Qt.CheckState.Unchecked
            )
        )

        self.buttonBox.button(QDialogButtonBox.StandardButton.Save).clicked.connect(self.save_settings)
        # self.buttonBox.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close_menu)
        

    def save_settings(self):
        # Default save directory
        save_dir = self.save_directory.text()

        if len(save_dir) == 0:
            save_dir = os.path.abspath("rataGUI_" + datetime.now().strftime('%H-%M-%S'))
            logger.warning(f"No save directory specified ... defaulting to {save_dir}")

        try:
            os.makedirs(os.path.normpath(save_dir), exist_ok=True)
        except Exception as err:
            logger.exception(err)
            logger.error(f"Invalid save directory specified")
            raise

        with open(os.path.join(save_dir, "config.json"), 'w') as file:
            config = {}
            config["Enabled Camera Modules"] = get_checked_names(self.camera_modules)
            config["Enabled Plugin Modules"] = get_checked_names(self.plugin_modules)
            config["Enabled Trigger Modules"] = get_checked_names(self.trigger_modules)
            config["Save Directory"] = save_dir
            config["FFMPEG Path"] = self.ffmpeg_path.text()
            json.dump(config, file, indent=2)

    
    # def close_menu(self):
    #     if 


def get_checked_names(check_list: QListWidget) -> list:
    checked = []
    for idx in range(check_list.count()):
        item = check_list.item(idx)
        if item.checkState() == Qt.CheckState.Checked:
            checked.append(item.text())
    return checked