# import sys
import time
import numpy as np
import nidaqmx
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
        self.trigger_thread = WorkerThread(self.run_trigger)
        self.threadpool.start(self.trigger_thread)

        # Instantiate plugins with camera-specific settings
        self.plugins = [Plugin(self, config) for Plugin, config in plugins]
        self.active = True

        # Start thread to load camera stream and start pipeline
        self.pipeline_thread = WorkerThread(self.start_camera_pipeline)
        self.threadpool.start(self.pipeline_thread)


    def run_trigger(self):
        device = "/Dev1/ao0"  # analog output channel name

        # Waveform paramters (volts)
        max_amplitude = 1.0 # max is ~2.5, amplitude of the signal 

        # Waveform parameters (seconds)
        rise_time = 0 # time until the max amplitude is reached
        duration = .01 # duration of max amplitude
        fall_time = 0 # time until max amplitude decays to 0
        # Other paramters
        isi = 5  # inter-waveform interval (in seconds)
        n = 10 # number of waveforms
        sample_rate = 1000000  # max sample rate supported by system

        rising_edge = np.linspace(0, max_amplitude, int(sample_rate * rise_time))
        high_component = max_amplitude * np.ones(int(sample_rate * duration))
        falling_edge = np.linspace(max_amplitude, 0, int(sample_rate * fall_time))
        blanks = np.zeros(int(4*sample_rate*duration))

        signal = np.concatenate((rising_edge, high_component, falling_edge, blanks))
        t = np.linspace(0,len(signal)/sample_rate, int(sample_rate*len(signal)))
        # 1. Create task
        with nidaqmx.Task() as task:
            # 2. Add analog output channel with safety voltage values
            task.ao_channels.add_ao_voltage_chan(device, min_val=-10, max_val=10)

            # 3. Modify sample clock rate to the max sample rate supported by the system, and tell it how many samples to output in finite mode
            task.timing.cfg_samp_clk_timing(sample_rate, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS, samps_per_chan=signal.shape[0])

            for i in range(n):
                # 4. Use auto_start to preload the signal (using task.start() will break the output signal)
                print('(%s) Output waveform %d/%d...' % (time(), i+1, n))
                task.write(signal, auto_start=True)

                # 5. Set the timeout of the task to the duration of the signal (without this the signal will instantly stop)
                # signal restarts automatically so a hack to avoid artifacts at the end
                # due to imprefectins in timing is to cut it short by 50ms
                time.sleep(rise_time + duration + fall_time )
                
                #task.write(np.zeros(1000), auto_start=True)
                # 6. Stop and cleanup the task
                task.stop()

                print('(%s) ISI for %d seconds' % (time(), isi))
                task.write(np.zeros(100), auto_start=True)
                time.sleep(.1)
                task.stop()
                time.sleep(isi)

        # Reset DC offset to zero
        with nidaqmx.Task() as task:
            task.ao_channels.add_ao_voltage_chan(device, min_val=-10, max_val=10)
            task.write([0.0, 0.0], auto_start=True)
            task.stop()

    async def acquire_frames(self):
        loop = asyncio.get_running_loop()
        while self.camera._running:
            # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
            if self.active:
                try:
                    status, frame = await loop.run_in_executor(None, self.camera.readCamera)
                    metadata = self.camera.getMetadata()
                    metadata['Timestamp'] = datetime.now()
                    metadata['CameraID'] = self.camera.getName()

                    if status: 
                        # Send acquired frame to first plugin process in pipeline
                        # print('Camera queue: ' + str(self.plugins[0].in_queue.qsize()))
                        await self.plugins[0].in_queue.put((frame, metadata))
                        await asyncio.sleep(0)
                    else:
                        raise IOError("Camera frame not found ... stopping")
                except Exception as err:
                    print('ERROR: %s' % err)
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

