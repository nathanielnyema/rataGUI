from triggers import BaseTrigger, ConfigManager

import nidaqmx

class NIDAQMXTrigger(BaseTrigger):
    """
    Interface for triggering connected National Instrument devices through the NI-DAQmx driver 
    """
    DEFAULT_CONFIG = {
        "FPS": 30, 
        "Phase offset (deg)": 0.0, 
    }

    @staticmethod
    def getAvailableDevices():
        '''Returns list of all available NI-DAQmx devices'''
        devices = []
        local_system = nidaqmx.system.System.local()
        for device in local_system.devices:
            # counter_names = [ci.name for ci in device.ci_physical_chans]
            devices.append(NIDAQMXTrigger(device))
        return devices

    def __init__(self, device):
        super().__init__(device.name)
        self.sub_devices = [ci.name for ci in device.ci_physical_chans]
        interval = 1

    def execute(self):
        print("NI-DAQmx triggered")
    
    def stop(self):
        pass