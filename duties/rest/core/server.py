"""Rest API server module
"""

from logging import getLogger
from multiprocessing import Process

from constants import logging
from uvicorn import Config as UvicornConfig
from uvicorn import Server as UvicornServer


class RestServer(Process):
    """Rest server in separate process

    Args:
        Process (_type_): Inherits from Process to start the sever in a separate process
    """

    def __init__(self, config: UvicornConfig) -> None:
        super().__init__()
        self.server = UvicornServer(config=config)
        self.config = config
        self.logger = getLogger()

    def stop(self) -> None:
        """Stops the rest server programatically"""
        self.terminate()

    def run(self) -> None:
        """Starts the rest server programatically"""
        self.logger.info(logging.START_REST_SERVER_MESSAGE, self.config.port)
        self.server.run()
        self.logger.error(logging.SYSTEM_EXIT_MESSAGE)
        self.logger.info(logging.MAIN_EXIT_MESSAGE)
