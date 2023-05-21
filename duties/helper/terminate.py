"""Helper module for graceful shutdown
"""

import signal
from asyncio import all_tasks, create_task, current_task, gather, get_running_loop
from sys import exit as sys_exit
from typing import List

from cli.types import Mode
from fetcher.data_types import ValidatorDuty


class GracefulTerminator:
    """Helper class for graceful termination"""

    def __init__(self, max_number_of_cicd_cycles: int) -> None:
        self.__cicd_cycle_counter = 0
        self.__max_number_of_cicd_cycles = max_number_of_cicd_cycles

    async def create_signal_handlers(self) -> None:
        """Creates signal handlers for common signals"""
        loop = get_running_loop()
        for signal_name in ("SIGINT", "SIGTERM"):
            loop.add_signal_handler(
                getattr(signal, signal_name), lambda: create_task(self.__shutdown())
            )

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

    async def __shutdown(self) -> None:
        """Cancels the task and raises exception if user generated SIGINT or SIGTERM is detected"""
        tasks = [task for task in all_tasks() if task is not current_task()]
        for task in tasks:
            task.cancel()
        await gather(*tasks, return_exceptions=True)
