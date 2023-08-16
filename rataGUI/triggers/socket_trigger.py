from rataGUI.triggers.base_trigger import BaseTrigger, ConfigManager

import logging
logger = logging.getLogger(__name__)

class SocketTrigger(BaseTrigger):
    """
    Interface for publishing information to a socket
    """
    DEFAULT_CONFIG = {
        "Server IP": "127.0.0.1",
        "Socket Port": "1234",
    }

    @staticmethod
    def getAvailableDevices():
        '''Returns list of test trigger(s)'''
        return [SocketTrigger("Socket Trigger 1")]

    def __init__(self, deviceID):
        super().__init__(deviceID)
        self.interval = -1


    def initialize(self, config: ConfigManager):
        self.initialized = True
        return True


    def execute(self):
        logger.info(f"Trigger: {str(self.deviceID)} executed")
    
    
    def close(self):
        logger.info("Test trigger stopped")
        self.initialized = False