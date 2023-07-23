from plugins import BasePlugin, ConfigManager

import os
import cv2
import numpy as np

class MetadataWriter(BasePlugin):
    """
    Plugin that overlays metadata onto frames and/or into a log file
    """
    DEFAULT_CONFIG = {
        'Overlay Timestamp': False,
        'Overlay Frame Index': False,
    }

    def __init__(self, cam_widget, config, queue_size=0):
        super().__init__(cam_widget, config, queue_size)

        print("Started Metadata Writer for: {}".format(cam_widget.camera.cameraID))
            

    def execute(self, frame, metadata):

        img_h, img_w, num_ch = frame.shape

        for idx, (name, value) in enumerate(metadata.items()):
            key = 'Overlay ' + name
            if self.config.get(key):
                if name == "Timestamp":
                    overlay = value.strftime('%H:%M:%S.%f')
                else:
                    overlay = name+": "+str(value)
                
                (text_w, text_h), _ = cv2.getTextSize(overlay, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75, thickness=2)
                pos = (5, img_h - idx*(text_h+2))
                cv2.rectangle(frame, pos, (pos[0] + text_w, pos[1] - text_h), (0, 0, 0), cv2.FILLED)
                cv2.putText(frame, overlay, pos, cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_4)

        return frame, metadata

    def close(self):
        print("Metadata writer closed")
        self.active = False