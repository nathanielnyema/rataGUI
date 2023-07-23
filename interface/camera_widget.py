# import sys
# import numpy as np
# import cv2
import os
from datetime import datetime
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
    """Encapsulates camera object and its plugin processing pipeline by connecting Camera and Plugin APIs.

    :param camera: Camera object to extract frames from
    :param cam_config: ConfigManager that stores camera settings
    :param plugins: List of plugin types in processing pipeline
    """

    def __init__(self, camera=None, cam_config=None, plugins=[]):
        super().__init__()
        self.setupUi(self)

        # Set widget fields
        self.frame_width = self.frameGeometry().width()
        self.frame_height = self.frameGeometry().height()

        # Initialize camera object
        self.camera = camera
        self.camera_model = type(camera).__name__
        self.camera_config = cam_config

        # Create GUI threadpool
        self.threadpool = QThreadPool().globalInstance()

        # Instantiate plugins with camera-specific settings
        self.plugins = [Plugin(self, config) for Plugin, config in plugins]
        self.active = True

        # Start thread to load camera stream and start pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)
        self.threadpool.start(self.pipeline_thread)

    async def acquire_frames(self):
        loop = asyncio.get_running_loop()
        while self.camera._running:
            # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
            if self.active:
                status, frame = await loop.run_in_executor(None, self.camera.readCamera)
                metadata = self.camera.getMetadata()
                metadata['Timestamp'] = datetime.now()

                if status: 
                    # Send acquired frame to first plugin process in pipeline
                    # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
                    await self.plugins[0].in_queue.put((frame, metadata))
                    await asyncio.sleep(0)
                else:
                    print("ERROR: camera frame not found ... stopping")
                    break
            else: # Pass to next coroutine
                await asyncio.sleep(0)

        # Close camera if camera stops streaming
        self.camera.closeCamera()

    async def process_plugin_pipeline(self):
        # Add process to continuously acquire frames from camera
        acquisition_task = asyncio.create_task(self.acquire_frames())

        # Add all plugin processes (pipeline) to async event loop
        plugin_tasks = [] 
        for cur_plugin, next_plugin in zip(self.plugins, self.plugins[1:]):
            # Connect outputs and inputs of consecutive plugin pairs
            cur_plugin.out_queue = next_plugin.in_queue
            plugin_tasks.append(asyncio.create_task(plugin_process(cur_plugin)))
        # Add terminating plugin
        plugin_tasks.append(asyncio.create_task(plugin_process(self.plugins[-1])))

        # Wait until camera stops running
        await acquisition_task

        # Wait for plugins to finish processing
        for plugin in self.plugins:
            await plugin.in_queue.join()

        # Cancel idle plugin processes
        for task in plugin_tasks:
            task.cancel()

    def stop_plugin_pipeline(self):
        for plugin in self.plugins:
            plugin.active = False

    def close_plugin_pipeline(self):
        for plugin in self.plugins:
            plugin.close()

    @pyqtSlot()
    def start_camera_pipeline(self):
        print('Started camera: {}'.format(self.camera.cameraID))
        self.camera.initializeCamera(self.camera_config)
        try:
            asyncio.run(self.process_plugin_pipeline(), debug=False)
        except Exception as err:
            print('ERROR: %s' % err)
            os._exit(42)

    def close_camera_pipeline(self):
        print('Stopped camera: {}'.format(self.camera.cameraID))
        # Signal to event loop to stop camera
        self.camera._running = False
        self.stop_plugin_pipeline()

    def close_widget(self):
        self.close_camera_pipeline()
        # Wait for thread to finish and queues to empty
        self.pipeline_thread.signals.finished.connect(self.close_plugin_pipeline)
        self.pipeline_thread.signals.finished.connect(self.deleteLater)

