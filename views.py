import sys
import numpy as np
import cv2
from vidgear.gears import WriteGear


from collections import deque
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from UI.MainWindow import Ui_MainWindow
from UI.CameraWindow import Ui_CameraWindow

from threads import CameraThread, WorkerThread
from cameras.WebCamera import WebCamera
from cameras.NetworkCamera import NetworkCamera
from cameras.FLIRCamera import FLIRCamera

class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    def __init__(self, cameraID):
        super().__init__()
        self.setupUi(self)

        self.window_width = self.frameGeometry().width()
        self.window_height = self.frameGeometry().height()

        self.cameraGrid = QtWidgets.QGridLayout()
        self.cameraGrid.setContentsMargins(0,0,0,0)
        self.setLayout(self.cameraGrid)


        cam0 = CameraWidget(self.window_width, self.window_height, cameraID, aspect_ratio=True)
        self.cameraGrid.addWidget(cam0)

    def startRecording(self, writer_params):
        widgets = (self.cameraGrid.itemAt(i).widget() for i in range(self.cameraGrid.count())) 
        for widget in widgets:
            if isinstance(widget, CameraWidget):
                widget.startWriter(writer_params)

    def clearLayout(self):
        while self.cameraGrid.count() > 0:
            camWidget = self.cameraGrid.takeAt(0).widget()
            if camWidget is not None:
                if camWidget.recording:
                    camWidget.stopWriter()
                camWidget.stopCameraThread()
                camWidget.deleteLater()

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)

        # Set geometry relative to screen
        sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
        window_width = sg.width() // 2
        window_height = int(sg.height() / 4.4)
        x_position = (sg.width() - window_width) // 2
        y_position = sg.height() - window_height
        self.setGeometry(x_position, y_position, window_width, window_height)

        self.cameras = []

        self.cameraWindow1 = None
        self.cameraWindow2 = None

        self.show_available_cameras()

        # Open and show camera feed but don't record
        self.displayButton.clicked.connect(self.show_camera_window)

        # Open, show and record camera feed into video
        self.recordButton.clicked.connect(self.record_camera_window)

        # Close camera feed (stop recording) and window
        self.stopButton.clicked.connect(self.close_camera_window)

    def show_available_cameras(self):
        cameraList = FLIRCamera.getCameraList()
        for i, camera in enumerate(cameraList):
            print(camera[])
            self.cameras.append(camera)
            

    def show_camera_window(self):
        if self.cameraWindow1 is None:
            # Specified video stream
            cameraID1 = "21129754"

            # Create separate thread and window for camera
            self.cameraWindow1 = CameraWindow(cameraID1)
            self.cameraWindow1.show()

            #Set geometry relative to screen
            sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            window_width = sg.width() // 2
            window_height = int(sg.height() / 1.5)
            x_position = (sg.width() - window_width) // 2
            y_position = self.pos().y() - window_height
            self.cameraWindow1.setGeometry(x_position, y_position, window_width, window_height)

            cameraID2 = "19173292"

            self.cameraWindow2 = CameraWindow(cameraID2)
            self.cameraWindow2.show()

            #Set geometry relative to screen
            sg = QtGui.QGuiApplication.primaryScreen().availableGeometry()
            window_width = sg.width() // 2
            window_height = int(sg.height() / 1.5)
            x_position = (sg.width() - window_width) // 2
            y_position = self.pos().y() - window_height
            self.cameraWindow2.setGeometry(x_position, y_position, window_width, window_height)
            
        else:
            self.cameraWindow1.show()
            self.cameraWindow2.show()


    def record_camera_window(self):
        self.show_camera_window()
        # params = {"-vcodec": "libx264", "-crf": 0, "-preset": "fast"}
        params = {}
        self.cameraWindow1.startRecording(writer_params=params)
        


    def close_camera_window(self):
        if self.cameraWindow1 is not None:
            self.cameraWindow1.clearLayout()
            self.cameraWindow1.deleteLater()
            self.cameraWindow1 = None

        if self.cameraWindow2 is not None:
            self.cameraWindow2.clearLayout()
            self.cameraWindow2.deleteLater()
            self.cameraWindow2 = None



class CameraWidget(QtWidgets.QWidget):
    """Independent camera feed
    Uses threading to grab IP camera frames in the background

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param stream_link - IP/RTSP/Webcam link
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, width, height, streamID=0, cameraType="flir", aspect_ratio=False, deque_size=1):
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

        # Create camera wrapper object
        self.camera_stream_link = streamID
        match cameraType:
            case "network":
                self.camera = NetworkCamera(streamID)
            case "web":
                self.camera = WebCamera(streamID)
            case "flir":
                self.camera = FLIRCamera(streamID)

        # Start thread to load camera stream
        worker = WorkerThread(self.camera.initializeCamera)
        self.threadpool.start(worker)
        worker.signals.finished.connect(self.startCameraThread)

        # Periodically set video frame to display
        self.timer = QTimer()
        self.timer.timeout.connect(self.set_frame)
        self.timer.start(50)

        print('Started camera: {}'.format(self.camera_stream_link))

    @pyqtSlot()
    def startCameraThread(self):
        # Start thread for frame grabbing
        self.cameraThread = CameraThread(self.camera, self.frames)
        self.threadpool.start(self.cameraThread)

    def stopCameraThread(self):
        print('Stopped camera: {}'.format(self.camera_stream_link))
        self.cameraThread.stop()

    def startWriter(self, output_params):
        # TODO: implement as custom class
        def save_frames():
            while self.recording:
                if len(self.frames) == 0:
                    continue

                self.writer.write(self.frames[-1], rgb_mode=True)
            
            # Close writer after thread is stopped
            self.writer.close()
        
        print("Started writer")
        file_name = datetime.now().strftime('%H,%M,%S')+".mp4"
        # file_name = "output.mp4"
        self.writer = WriteGear(output_filename=file_name, logging=True, **output_params)
        self.recording = True

        worker = WorkerThread(save_frames)
        self.threadpool.start(worker)

    def stopWriter(self):
        self.recording = False

    def set_frame(self):
        """Sets pixmap image to video frame"""

        if self.frames and self.camera._running:
            # Grab latest frame
            image = self.frames[-1]

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
