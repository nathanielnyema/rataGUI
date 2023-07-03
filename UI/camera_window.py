import sys
import numpy as np
import cv2
# import logging
# import time

# from vidgear.gears import WriteGear
import skvideo.io
# skvideo.setFFmpegPath("C:/PATH_Programs/bin/ffmpeg.exe")

from collections import deque
from datetime import datetime

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from threads import WorkerThread
from UI.design.Ui_CameraWindow import Ui_CameraWindow

import asyncio
# from concurrent.futures import ThreadPoolExecutor

# Change to camera widget
class CameraWindow(QtWidgets.QWidget, Ui_CameraWindow):
    """Independent camera feed

    @param width - Width of the video frame
    @param height - Height of the video frame
    @param camera - Camera object to display
    @param aspect_ratio - Whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, camera=None, plugins=[], aspect_ratio=True, queue_size = 100):
        super().__init__()
        self.setupUi(self)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()
        self.keep_aspect_ratio = aspect_ratio
        self.recording = False

        # Create camera GUI layout TODO: Make in qt designer
        self.video_frame = QtWidgets.QLabel(self)
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(self.video_frame)
        self.setLayout(self.layout)

        # Initialize camera object
        self.camera = camera
        self.camera_model = type(camera).__name__

        # Create GUI threadpool
        self.threadpool = QThreadPool().globalInstance()

        # TODO: Instantiate plugins with camera-specific settings
        self.plugins = [Plugin(self) for Plugin in plugins]

        # Start thread to load camera stream
        worker = WorkerThread(self.camera.initializeCamera)
        worker.signals.finished.connect(self.startPipelineThread)
        self.threadpool.start(worker)

    async def acquire_frames(self):
        loop = asyncio.get_running_loop()
        while self.camera._running:
            status, frame = await loop.run_in_executor(None, self.camera.readCamera)
            # status, frame = self.camera.readCamera("RGB")
            if status: 
                # print("Acquired Frame: " + str(self.camera.frames_acquired))
                await self.plugins[0].in_queue.put(frame)
                await asyncio.sleep(0)
            else:
                print("Error: camera frame not found ... stopping")
                self.camera.stopCamera()

    async def startPluginPipeline(self):
        # Add all plugin processes (pipeline) to async event loop
        for cur_plugin, next_plugin in zip(self.plugins, self.plugins[1:]):
            # Connect outputs and inputs of consecutive plugin pairs
            cur_plugin.out_queue = next_plugin.in_queue
            asyncio.create_task(plugin_process(next_plugin))
        # Add terminating plugin
        asyncio.create_task(plugin_process(self.plugins[-1]))

        # Send frames through pipeline
        await self.acquire_frames()
        for plugin in self.plugins:
            await plugin.in_queue.join()


    async def stopPluginPipeline(self):
        pass

    @pyqtSlot()
    def startPipelineThread(self):
        assert(len(self.plugins) > 0)

        print('Started camera: {}'.format(self.camera.cameraID))
        self.pipeline_thread = WorkerThread(asyncio.run, self.startPluginPipeline())
        self.threadpool.start(self.pipeline_thread)

    def stopCameraThread(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        self.camera.stopCamera()

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


async def plugin_process(plugin):
    while True:
        frame = await plugin.in_queue.get()

        # TODO: Add plugin-specific data

        # TODO: Parallelize with Thread Executor

        # Execute plugin
        result = plugin.execute(frame)
        # Load output to 
        if plugin.out_queue != None:
            await plugin.out_queue.put(result)
        
        plugin.in_queue.task_done()