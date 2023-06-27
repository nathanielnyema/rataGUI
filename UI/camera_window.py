import sys
import numpy as np
import cv2

# from vidgear.gears import WriteGear
import skvideo.io
# skvideo.setFFmpegPath("C:/PATH_Programs/bin/ffmpeg.exe")

from collections import deque
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from threads import CameraThread, WorkerThread
from UI.design.Ui_CameraWindow import Ui_CameraWindow

class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    """Independent camera feed

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param camera - Camera object to display
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, camera=None, aspect_ratio=True, deque_size=100):
        super().__init__()
        self.setupUi(self)
        
        # Initialize deque used to store frames read from the stream
        self.frames = deque(maxlen=deque_size)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()
        self.keep_aspect_ratio = aspect_ratio
        self.recording = False

        # Create camera GUI layout
        self.video_frame = QtWidgets.QLabel(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.video_frame)
        self.setLayout(self.layout)

        # Create threadpool for video streaming
        self.threadpool = QThreadPool().globalInstance()

        # Initialize camera object
        self.camera_type = type(camera).__name__
        self.camera = camera
        self.camera_thread = CameraThread(self.camera, self.frames)

        # Start thread to load camera stream
        worker = WorkerThread(self.camera.initializeCamera)
        self.threadpool.start(worker)
        worker.signals.finished.connect(self.startCameraThread)

        # Could use separate timer instead
        # self.timer = QTimer()
        # self.timer.timeout.connect(self.set_frame)
        # self.timer.start(100)

        print('Started camera: {}'.format(self.camera.cameraID))

    @pyqtSlot()
    def startCameraThread(self):
        # Periodically set video frame to display
        self.camera_thread.signals.result.connect(self.set_frame)
        # Start camera thread for frame grabbing
        self.threadpool.start(self.camera_thread)

    def stopCameraThread(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        self.camera_thread.stop()

    def startWriter(self, output_params):
        # TODO: implement as custom class
        # TODO: implement pause functionality
        def save_frames():
            # Waits until all frames are saved
            # Alternatively, I could always leave one frame available up until recording stops
            while self.recording or len(self.frames) > 0:
                if len(self.frames) == 0:
                    # print("Warning: No frame available to save")
                    continue
                
                #Write oldest frame in queue
                self.writer.writeFrame(self.frames.popleft())
            
            # Close writer after thread is stopped
            self.writer.close()
        
        print("Started recording for: {}".format(self.camera.cameraID))
        file_name = "videos/" + str(self.camera.cameraID) + "_" + datetime.now().strftime('%H-%M-%S') + ".mp4"
        # file_name = "output.mp4"
        # self.writer = WriteGear(output_filename=file_name, logging=True, **output_params)
        # TODO: Modularize parameters
        input_params = {}
        # if self.camera_type == "FLIRCamera":
        #     input_params['-framerate'] = str(FLIRCamera.CameraProperties['AcquisitionFrameRate'])
        self.writer = skvideo.io.FFmpegWriter(file_name, inputdict=input_params, outputdict=output_params)
        self.recording = True
        self.camera_thread._recording = True

        worker = WorkerThread(save_frames)
        self.threadpool.start(worker)

    def stopWriter(self):
        print("Stopped recording for: {}".format(self.camera.cameraID))
        self.recording = False
        self.camera_thread._recording = False

    def set_frame(self, image):
        """Sets pixmap image to video frame"""

        if self.camera._running:
            # Get image dimensions
            img_h, img_w, num_ch = image.shape

            # TODO: Add timestamp to frame
            cv2.rectangle(image, (img_w-190,0), (img_w,50), color=(0,0,0), thickness=-1)
            cv2.putText(image, datetime.now().strftime('%H:%M:%S'), (img_w-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            bytes_per_line = num_ch * img_w
            qt_image = QtGui.QImage(image.data, img_w, img_h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
            qt_image = qt_image.scaled(self.frame_width, self.frame_height, Qt.AspectRatioMode.KeepAspectRatio)
            pixmap = QtGui.QPixmap.fromImage(qt_image)
            self.video_frame.setPixmap(pixmap)