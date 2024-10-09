"""Rest API server module
"""

import socket as sock
from logging import getLogger
from multiprocessing import Process

from cli.arguments import ARGUMENTS
from constants import logging
from uvicorn import Config as UvicornConfig
from uvicorn import Server as UvicornServer


class RestServer(Process):
    """Rest server in separate process

    Args:
        config (UvicornConfig): Uvicorn config
    """

    def __init__(self, config: UvicornConfig) -> None:
        super().__init__()
        self.server = UvicornServer(config=config)
        self.config = config
        self.logger = getLogger()
        self.started = False

    def stop(self) -> None:
        """Stops the rest server programatically"""
        self.terminate()

    def run(self) -> None:
        """Start the rest server programatically"""
        if not self.__is_port_in_use():
            self.logger.info(logging.START_REST_SERVER_MESSAGE, self.config.port)
            self.server.run()

    def __is_port_in_use(self) -> bool:
        """Check if defined port for rest server is already in use

        Returns:
            bool: Is defined port already in use
        """
        socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        destination = ("127.0.0.1", ARGUMENTS.rest_port)
        connection_result = socket.connect_ex(destination)
        if connection_result == 0:
            self.logger.error(
                logging.PORT_ALREADY_IN_USAGE_MESSAGE, ARGUMENTS.rest_port
            )
            socket.close()
            return True
        socket.close()
        return False
