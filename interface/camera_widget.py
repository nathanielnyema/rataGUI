# import sys
# import numpy as np
# import cv2
import time
# import logging

from plugins import plugin_process

from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QThreadPool, QObject, QTimer, pyqtSlot, pyqtSignal, QRect

from threads import WorkerThread
from interface.design.Ui_CameraWidget import Ui_CameraWidget

import asyncio
# from concurrent.futures import ThreadPoolExecutor

# Change to camera widget
class CameraWidget(QtWidgets.QWidget, Ui_CameraWidget):
    """Independent camera feed

    @param width - width of the video frame
    @param height - height of the video frame
    @param camera - camera object to display
    @param aspect_ratio - whether to maintain frame aspect ratio or force into fraame
    """

    def __init__(self, camera=None, plugins=[]):
        super().__init__()
        self.setupUi(self)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()

        # Initialize camera object
        self.camera = camera
        self.camera_model = type(camera).__name__

        # Create GUI threadpool
        self.threadpool = QThreadPool().globalInstance()

        # TODO: Instantiate plugins with camera-specific settings
        self.plugins = [Plugin(self) for Plugin in plugins]
        self.active = True
        # self.keep_aspect_ratio = aspect_ratio

        # Start thread to load camera stream and start pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)
        self.threadpool.start(self.pipeline_thread)

    async def acquire_frames(self):
        loop = asyncio.get_running_loop()
        while self.camera.isOpened():
            
            if self.active:
                status, frame = await loop.run_in_executor(None, self.camera.readCamera)
                # status, frame = self.camera.readCamera("RGB")
                if status: 
                    # Send acquired frame to first plugin process in pipeline
                    await self.plugins[0].in_queue.put(frame)
                    await asyncio.sleep(0)
                else:
                    print("Error: camera frame not found ... stopping")
                    break
            else: # Pass to next coroutine
                await asyncio.sleep(0)

        # Close camera if camera stops streaming
        self.camera.closeCamera()

    async def process_plugin_pipeline(self):
        # Add all plugin processes (pipeline) to async event loop
        for cur_plugin, next_plugin in zip(self.plugins, self.plugins[1:]):
            # Connect outputs and inputs of consecutive plugin pairs
            cur_plugin.out_queue = next_plugin.in_queue
            asyncio.create_task(plugin_process(cur_plugin))
        # Add terminating plugin
        asyncio.create_task(plugin_process(self.plugins[-1]))

        # Send frames through pipeline
        await self.acquire_frames()
        for plugin in self.plugins:
            await plugin.in_queue.join()
        

    def stop_plugin_pipeline(self):
        for plugin in self.plugins:
            plugin.active = False

    @pyqtSlot()
    def start_camera_pipeline(self):
        print('Started camera: {}'.format(self.camera.cameraID))
        self.camera.initializeCamera()
        asyncio.run(self.process_plugin_pipeline())

    def close_camera_pipeline(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        # Signal to event loop to stop camera
        self.camera._running = False
        self.stop_plugin_pipeline()

    def close_widget(self):
        self.close_camera_pipeline()
        # Wait for thread to finish and queues to empty
        self.pipeline_thread.signals.finished.connect(self.deleteLater)
