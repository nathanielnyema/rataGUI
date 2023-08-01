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
        pass

    def __init__(self, config: ConfigManager):
        pass

    def execute(self):
        print("NI-DAQmx triggered")
    
    def stop(self):
        pass