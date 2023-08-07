import traceback, sys
import numpy as np
import time

import cv2

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QRunnable, QObject, QTimer, pyqtSlot, pyqtSignal

class ThreadSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)


class WorkerThread(QRunnable):
    '''
    Worker that runs an arbitrary function in QThreadPool.
    
    Emits finished, error and result pyqtSignals.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, func, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = ThreadSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.func(*self.args, **self.kwargs)
        except:
            traceback.print_exc() # TODO: Understand error handling
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the process
        finally:
            self.signals.finished.emit()  # Done