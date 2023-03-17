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
    # next_frame = pyqtSignal(np.ndarray)


class WorkerThread(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
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
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done

class CameraThread(QRunnable):

    DEFAULT_DISPLAY_INTERVAL = 5

    def __init__(self, camera, deque):
        super().__init__()
        self.signals = ThreadSignals()
        self._running = True
        self.stream = camera
        self.frames = deque
        self.count = 0

        # Controls display frame rate
        self.DISPLAY_INTERVAL = -1

    @pyqtSlot()
    def run(self):
        
        while self._running:
            try:
                if self.stream._running:
                    status, frame = self.stream.readCamera("RGB")
                    if status:
                        self.frames.append(frame)
                        self.count += 1

                        if self.DISPLAY_INTERVAL > 0 and self.count % self.DISPLAY_INTERVAL == 0:
                            self.signals.result.emit(frame)
                    else:
                        self.stream.stopCamera()
                else:
                    print('Attempting to reconnect camera:', str(self.stream.getCameraID()))
                    self.stream.initializeCamera()
                    time.sleep(2)
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))

        # Close camera after thread is stopped
        self.stream.stopCamera()


    def stop(self):
        self._running = False


# class WriterThread(QRunanble):
# 
    # def __init__(self, camera, deque):
        # super().__init__()
        # self.signals = ThreadSig