"""Helper module for graceful shutdown
"""

import signal
from typing import Any


class GracefulKiller:
    """Helper class for graceful shutdown"""

    kill_now = False

    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.__exit_gracefully)
        signal.signal(signal.SIGTERM, self.__exit_gracefully)

    def __exit_gracefully(self, *args: Any) -> None:
        """Main method to exit program gracefully"""
        self.kill_now = True
