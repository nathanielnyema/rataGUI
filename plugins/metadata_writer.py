# from plugins import BasePlugin, ConfigManager

# import os
# import cv2
# import numpy as np

# from datetime import datetime

# class MetadataWriter(BasePlugin):
#     """
#     Plugin that overlays metadata onto frames and/or into a log file
#     """

#     def __init__(self, cam_widget, config, queue_size=0):
#         super().__init__(cam_widget, config, queue_size)

#         print("Started Metadata Writer for: {}".format(cam_widget.camera.cameraID))

#     def execute(self, frame, metadata):

#         img_h, img_w, num_ch = frame.shape

#         if self.config.get('save timestamp'):
#             cv2.rectangle(frame, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
#             cv2.putText(frame, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)
