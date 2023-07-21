from plugins import BasePlugin, ConfigManager

import cv2
from datetime import datetime
from PyQt6 import QtGui
from PyQt6.QtCore import Qt

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
        
        print("Started Frame Display for: {}".format(cam_widget.camera.cameraID))
        self.video_frame = cam_widget.video_frame
        self.frame_width = cam_widget.frame_width
        self.frame_height = cam_widget.frame_height


    def execute(self, frame, metadata):
        """Sets pixmap image to video frame"""
        # print("frame displayed")

        # print(self.in_queue.qsize())

        # Get image dimensions
        img_h, img_w, num_ch = frame.shape

        if self.config.get('Show timestamp'):
            cv2.rectangle(frame, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
            cv2.putText(frame, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

        # Convert to pixmap and set to video frame
        bytes_per_line = num_ch * img_w
        qt_image = QtGui.QImage(frame.data, img_w, img_h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        if self.config.get('Keep aspect ratio'):
            qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.KeepAspectRatio)
        else: 
            qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.IgnoreAspectRatio)
        
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self.video_frame.setPixmap(pixmap)
        
        return frame, metadata

    def close(self):
        print("Frame display closed")
        self.active = False
