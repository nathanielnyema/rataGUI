from rataGUI.triggers.base_trigger import BaseTrigger, ConfigManager

import time
import socket

import logging

logger = logging.getLogger(__name__)


class UDPSocket(BaseTrigger):
    """
    Interface for publishing information to a socket
    """

    DEFAULT_CONFIG = {
        "Server IP": "127.0.0.1",
        "Socket Port": 1234,
    }

    @staticmethod
    def getAvailableDevices():
        """Returns list of test trigger(s)"""
        return [UDPSocket(f"Rasberry Pi {i+1}") for i in range(1)]

    def __init__(self, deviceID):
        super().__init__(deviceID)
        self._socket = None

    def initialize(self, config: ConfigManager):
        self.server_ip = config.get("Server IP")
        self.port = config.get("Socket Port")
        self._socket = socket.socket(socket.AF_INET, type=socket.SOCK_DGRAM)
        self._socket.settimeout(1.0)

        # self.count = 0

        self.initialized = True
        return True

    def execute(self, signal: str):
        try:
            # self.count += 1
            # print(self.count, time.time())
            if self.initialized:
                self._socket.sendto(
                    bytes(signal, encoding="utf-8"), (self.server_ip, self.port)
                )

            # logger.info(f"Trigger: {str(self.deviceID)} executed")
        except Exception as err:
            logger.exception(err)
            logger.info(f"Trigger: {str(self.deviceID)} failed to execute")

    def close(self):
        logger.info("Test trigger stopped")
        self._socket.close()
        self.initialized = False
