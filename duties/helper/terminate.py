"""Helper module for graceful shutdown
"""

import signal
from asyncio import all_tasks, create_task, current_task, gather, get_running_loop
from logging import getLogger
from sys import exit as sys_exit
from typing import List

from cli.arguments import ARGUMENTS
from cli.types import Mode
from constants import logging
from fetcher.data_types import DutyType, ValidatorDuty
from helper.help import clean_shared_memory, get_duties_proportion_above_time_threshold


class GracefulTerminator:
    """Helper class for graceful termination"""

    def __init__(self, max_number_of_cicd_cycles: int) -> None:
        self.__cicd_cycle_counter = 0
        self.__max_number_of_cicd_cycles = max_number_of_cicd_cycles
        self.logger = getLogger()

    async def create_signal_handlers(self) -> None:
        """Creates signal handlers for common signals"""
        loop = get_running_loop()
        for signal_name in ("SIGINT", "SIGTERM"):
            loop.add_signal_handler(
                getattr(signal, signal_name), lambda: create_task(self.__shutdown())
            )

    async def __shutdown(self) -> None:
        """Cancels the task and raises exception if user generated SIGINT or SIGTERM is detected"""
        tasks = [task for task in all_tasks() if task is not current_task()]
        for task in tasks:
            task.cancel()
        await gather(*tasks, return_exceptions=True)

    def terminate_in_cicd_mode(self, duties: List[ValidatorDuty]) -> None:
        """Terminates the running application in dependence of the mode and
        the duties which could be found for the provided validators

        Args:
            duties (List[ValidatorDuty]): List of fetched validator duties
        """
        running_mode: Mode = ARGUMENTS.mode
        match running_mode:
            case Mode.CICD_EXIT:
                if self.__no_relevant_upcoming_duties(duties):
                    self.logger.info(logging.EXIT_CODE_MESSAGE, 0)
                    clean_shared_memory()
                    sys_exit(0)
                self.logger.info(logging.EXIT_CODE_MESSAGE, 1)
                clean_shared_memory()
                sys_exit(1)
            case Mode.CICD_WAIT:
                if self.__no_relevant_upcoming_duties(duties):
                    self.logger.info(logging.EXIT_CODE_MESSAGE, 0)
                    clean_shared_memory()
                    sys_exit(0)
                if self.__cicd_cycle_counter >= self.__max_number_of_cicd_cycles:
                    self.logger.info(logging.EXIT_DUE_TO_MAX_WAITING_TIME_MESSAGE)
                    self.logger.info(logging.EXIT_CODE_MESSAGE, 1)
                    clean_shared_memory()
                    sys_exit(1)
            case Mode.CICD_FORCE_GRACEFUL_EXIT:
                clean_shared_memory()
                self.logger.info(logging.EXIT_CODE_MESSAGE, 0)
                sys_exit(0)
            case _:
                pass
        self.__cicd_cycle_counter += 1

    def __no_relevant_upcoming_duties(self, duties: List[ValidatorDuty]) -> bool:
        """Checks whether there are non relevant upcoming duties for the provided validators

        Args:
            duties (List[ValidatorDuty]): List of fetched validator duties

        Returns:
            bool: Whether or not there are any relevant upcoming duties
        """
        if len(duties) == 0:
            return True
        attestation_duties = [
            duty for duty in duties if duty.type == DutyType.ATTESTATION
        ]
        if len(attestation_duties) != len(duties):
            return False
        return self.__is_proportion_of_attestation_duties_above_time_threshold(
            attestation_duties
        )

    def __is_proportion_of_attestation_duties_above_time_threshold(
        self, attestation_duties: List[ValidatorDuty]
    ) -> bool:
        """Checks whether upcoming attestation duties will occur after a user definded
        time threshold and thus be defined as non-relevant duties

        Args:
            attestation_duties (List[ValidatorDuty]): List of fetched attestation duties

        Returns:
            bool: Whether or not there are any relevant upcoming attestation duties
        """
        relevant_duty_proportion = get_duties_proportion_above_time_threshold(
            attestation_duties, ARGUMENTS.mode_cicd_attestation_time
        )
        self.logger.info(
            logging.PROPORTION_OF_DUTIES_ABOVE_TIME_THRESHOLD_MESSAGE,
            round(relevant_duty_proportion * 100, 2),
            "attestation",
            ARGUMENTS.mode_cicd_attestation_time,
        )
        return relevant_duty_proportion >= ARGUMENTS.mode_cicd_attestation_proportion
