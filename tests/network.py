import cv2
from PyQt6.QtCore import Qt, QThread




# class NetworkWorker(QThread):

#     def __init__(self, streamID):
#         super().__init__()
#         self._running = True
#         self.streamID = streamID

#     def verify_network_stream(self, streamID):
#         """Attempts to receive a frame from given stream"""

#         cap = cv2.VideoCapture(streamID)
#         if not cap.isOpened():
#             return False
#         cap.release()
#         return True

#     def run(self):
#         if self.verify_network_stream(self.streamID):
#             self.stream = cv2.VideoCapture(self.streamID)
#             self.online = True
#     def stop(self):
#         """Sets run flag to False and waits for thread to finish"""
#         self._running = False
#         self.wait()