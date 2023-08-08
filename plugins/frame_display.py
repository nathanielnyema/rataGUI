from plugins import BasePlugin, ConfigManager

import cv2
from datetime import datetime
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class DisplaySignal(QObject):
    image = pyqtSignal(QtGui.QImage)

class FrameDisplay(BasePlugin):
    """
    Plugin that displays frames in a separate window.

    :param aspect_ratio: Whether to maintain frame aspect ratio or force into frame
    """
    DEFAULT_CONFIG = {
        'Keep aspect ratio': True,
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)
        
        print("Started Frame Display for: {}".format(cam_widget.camera.getName()))
        self.frame_width = cam_widget.frame_width
        self.frame_height = cam_widget.frame_height
        self.signal = DisplaySignal()
        self.signal.image.connect(cam_widget.set_window_pixmap)


    def process(self, frame, metadata):
        """Sets pixmap image to video frame"""
        # print("frame displayed")

        # print(self.in_queue.qsize())

        # Get image dimensions
        img_h, img_w, num_ch = frame.shape

        # Convert to pixmap and set to video frame
        bytes_per_line = num_ch * img_w
        qt_image = QtGui.QImage(frame.data, img_w, img_h, bytes_per_line, QtGui.QImage.Format.Format_RGB888).copy()
        if self.config.get('Keep aspect ratio'):
            qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.KeepAspectRatio)
        else: 
            qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.IgnoreAspectRatio)
        
        self.signal.image.emit(qt_image)
        
        return frame, metadata

    def close(self):
        print("Frame display closed")
        self.active = False
