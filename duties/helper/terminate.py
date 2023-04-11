"""Helper module for graceful shutdown
"""

import signal
from sys import exit as sys_exit
from typing import Any, List

from cli.types import Mode
from fetcher.data_types import ValidatorDuty


# pylint: disable=too-few-public-methods
class GracefulTerminator:
    """Helper class for graceful termination"""

    def __init__(self, max_number_of_cicd_cycles: int) -> None:
        self.kill_now = False
        self.__cicd_cycle_counter = 0
        self.__max_number_of_cicd_cycles = max_number_of_cicd_cycles
        signal.signal(signal.SIGINT, self.__terminate_gracefully)
        signal.signal(signal.SIGTERM, self.__terminate_gracefully)

    def __terminate_gracefully(self, *_: Any) -> None:
        """Main method to terminate program gracefully"""
        self.kill_now = True

    def terminate_in_cicd_mode(
        self, running_mode: Mode, duties: List[ValidatorDuty]
    ) -> None:
        """Terminates the running application in dependence of the mode and
        the duties which could be found for the provided validators

        Args:
            running_mode (Mode): Running mode of eth-duties
            duties (List[ValidatorDuty]): List of fetched validator duties
        """
        match running_mode:
            case Mode.CICD_EXIT:
                if len(duties) > 0:
                    sys_exit(1)
                sys_exit(0)
            case Mode.CICD_WAIT:
                if len(duties) == 0:
                    sys_exit(0)
                if self.__cicd_cycle_counter >= self.__max_number_of_cicd_cycles:
                    sys_exit(1)
            case Mode.EXIT_GRACEFULLY:
                sys_exit(0)
            case _:
                pass
        self.__cicd_cycle_counter += 1
