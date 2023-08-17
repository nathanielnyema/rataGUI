# import sys
import time
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from rataGUI.utils import WorkerThread
from rataGUI.interface.design.Ui_StartMenu import Ui_StartMenu

import asyncio
from concurrent.futures import ThreadPoolExecutor

import logging
logger = logging.getLogger(__name__)

# process_pool = ProcessPoolExecutor()
thread_pool = ThreadPoolExecutor()

EXP_AVG_DECAY = 0.8

class StartMenu(QtWidgets.QDialog, Ui_StartMenu):

    def __init__(self):
        super().__init__()
        self.setupUi(self)