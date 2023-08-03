from triggers import BaseTrigger, ConfigManager

import nidaqmx

class NIDAQmxCounter(BaseTrigger):
    """
    Interface for triggering connected National Instrument devices through the NI-DAQmx driver 
    """
    DEFAULT_CONFIG = {
        "FPS": 30, 
        "Phase offset (deg)": 0.0, 
    }

    @staticmethod
    def getAvailableDevices():
        '''Returns list of all available NI-DAQmx counter channels'''
        counter_channels = []
        local_system = nidaqmx.system.System.local()
        for device in local_system.devices:
            counter_channels.extend([NIDAQmxCounter(co.name) for co in device.co_physical_chans])
        return counter_channels

    def __init__(self, deviceID):
        super().__init__(deviceID)

        self.interval = 1

    def initialize(self, config: ConfigManager):
        pass

    def execute(self):
        print("NI-DAQmx triggered")
    
    def stop(self):
        pass