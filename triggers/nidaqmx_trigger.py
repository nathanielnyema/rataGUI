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

