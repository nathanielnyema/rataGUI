from triggers import BaseTrigger, ConfigManager

import logging
logger = logging.getLogger(__name__)

class TemplateTrigger(BaseTrigger):
    """
    Interface for triggering connected National Instrument devices through the NI-DAQmx driver.

    Current implementation produces TTL pulses to trigger cameras at specified FPS and phase.
    """
    DEFAULT_CONFIG = {
    }

    @staticmethod
    def getAvailableDevices():
        '''Returns list of test trigger(s)'''
        return [TemplateTrigger("test1")]

    def __init__(self, deviceID):
        super().__init__(deviceID)
        self.interval = -1


    def initialize(self, config: ConfigManager):
        self.initialized = True


    def execute(self):
        logger.info(f"Trigger: {str(self.deviceID)} executed")
    
    
    def close(self):
        logger.info("Test trigger stopped")
        self.initialized = False