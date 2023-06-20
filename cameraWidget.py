import numpy as np
import cv2

# import skvideo
# skvideo.setFFmpegPath("C:/PATH_Programs/bin/ffmpeg.exe")
import skvideo.io

from collections import deque
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from threads import CameraThread, WorkerThread
from cameras.WebCamera import WebCamera
from cameras.NetworkCamera import NetworkCamera
from cameras.FLIRCamera import FLIRCamera

class CameraWidget(QtWidgets.QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, width, height, camera=None, cameraType="flir", aspect_ratio=False, deque_size=100):
        super().__init__()
        
        # Initialize deque used to store frames read from the stream
        self.frames = deque(maxlen=deque_size)

        # Set widget fields
        self.frame_width = width
        self.frame_height = height
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
        self.camera_type = cameraType
        self.camera = camera
        self.cameraThread = CameraThread(self.camera, self.frames)

        # Start thread to load camera stream
        worker = WorkerThread(self.camera.initializeCamera, FLIRCamera.CameraProperties)
        self.threadpool.start(worker)
        worker.signals.finished.connect(self.startCameraThread)

        # self.timer = QTimer()
        # self.timer.timeout.connect(self.set_frame)
        # self.timer.start(100)

        print('Started camera: {}'.format(self.camera.cameraID))

    @pyqtSlot()
    def startCameraThread(self):
        # Periodically set video frame to display
        self.cameraThread.signals.result.connect(self.set_frame)
        # Start camera thread for frame grabbing
        self.threadpool.start(self.cameraThread)

    def stopCameraThread(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        self.cameraThread.stop()

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
        file_name = "videos/" + str(self.camera.cameraID) + "_" + datetime.now().strftime('%H,%M,%S') + ".mp4"
        # file_name = "output.mp4"
        # self.writer = WriteGear(output_filename=file_name, logging=True, **output_params)
        input_params={'-framerate': str(FLIRCamera.CameraProperties['AcquisitionFrameRate'])} 
        self.writer = skvideo.io.FFmpegWriter(file_name, inputdict=input_params, outputdict=output_params)
        self.recording = True
        self.cameraThread._recording = True

        worker = WorkerThread(save_frames)
        self.threadpool.start(worker)

    def stopWriter(self):
        print("Stopped recording for: {}".format(self.camera.cameraID))
        self.recording = False
        self.cameraThread._recording = False

    def startDisplay(self):
        # if self.cameraThread is not None:
        self.cameraThread.DISPLAY_INTERVAL = CameraThread.DEFAULT_DISPLAY_INTERVAL

    def stopDisplay(self):
        # if self.cameraThread is not None:
        self.cameraThread.DISPLAY_INTERVAL = -1

    def set_frame(self, image):
        """Sets pixmap image to video frame"""

        if self.camera._running:
            # Get image dimensions
            img_h, img_w, num_ch = image.shape

            if self.keep_aspect_ratio:
                # Keep frame aspect ratio
                scale_factor = min(self.frame_width / img_w, self.frame_height / img_h)
                new_width = int(img_w * scale_factor)
                new_height = int(img_h * scale_factor)
                self.frame = cv2.resize(image, (new_width, new_height))

            else:
                # Force resize
                self.frame = cv2.resize(image, (self.frame_width, self.frame_height), interpolation = cv2.INTER_AREA)

            # Add timestamp to cameras
            cv2.rectangle(self.frame, (self.frame_width-190,0), (self.frame_width,50), color=(0,0,0), thickness=-1)
            cv2.putText(self.frame, datetime.now().strftime('%H:%M:%S'), (self.frame_width-185,37), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), lineType=cv2.LINE_AA)

            # Convert to pixmap and set to video frame
            self.img = QtGui.QImage(self.frame.data, self.frame.shape[1], self.frame.shape[0], QtGui.QImage.Format.Format_RGB888)
            self.pixmap = QtGui.QPixmap.fromImage(self.img)
            self.video_frame.setPixmap(self.pixmap)
