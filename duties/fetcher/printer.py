"""Module for printing validator duties
"""

# pylint: disable=import-error

from time import time, strftime, gmtime
from logging import getLogger
from typing import List
from colorama import Back, Style
from fetcher.data_types import ValidatorDuty, DutyType
from fetcher.constants import ethereum
from fetcher.constants import logging
from fetcher.constants import program


def print_time_to_next_duties(
    validator_duties: List[ValidatorDuty], genesis_time: int
) -> None:
    """Prints time to next duties for the provided validators

    Args:
        validator_duties (List[ValidatorDuty]): List of validator duties
        genesis_time (int): Genesis time of the connected chain
    """
    logger = getLogger(__name__)
    logger.info(logging.NEXT_INTERVAL_MESSAGE)
    if validator_duties:
        for index, duty in enumerate(validator_duties):
            now = time()
            seconds_to_next_duty = duty.slot * ethereum.SLOT_TIME + genesis_time - now
            logging_message = __create_logging_message(seconds_to_next_duty, duty)
            if index == len(validator_duties) - 1:
                logging_message += "\n"
            logger.info(logging_message)
    else:
        logger.info(logging.NO_UPCOMING_DUTIES_MESSAGE)


def __create_logging_message(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    """Creates the logging message for the provided duty

    Args:
        seconds_to_next_duty (float): Time to next duty in seconds
        duty (ValidatorDuty): Specific upcoming validator duty

    Returns:
        str: Message which will be logged to stdout
    """
    if seconds_to_next_duty < 0:
        logging_message = (
            f"Upcoming {duty.type.name} duty "
            f"for validator {duty.validator_index} outdated. "
            f"Fetching duties in next interval."
        )
    else:
        time_to_next_duty = strftime(
            program.PRINTER_TIME_FORMAT, gmtime(float(seconds_to_next_duty))
        )
        logging_message = (
            f"{__get_printing_color(seconds_to_next_duty, duty)}"
            f"Validator {duty.validator_index} has next {duty.type.name} duty in: "
            f"{time_to_next_duty} min. (slot: {duty.slot}){Style.RESET_ALL}"
        )
    return logging_message


def __get_printing_color(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    """Gets correct printing color in dependence of duty and time to next duty

    Args:
        seconds_to_next_duty (float): Time to next duty in seconds
        duty (ValidatorDuty): Specific upcoming validator duty

    Returns:
        str: ANSI codes for colorful logging
    """
    if (
        program.RED_PRINTING_THRESHOLD_IN_SECONDS
        < seconds_to_next_duty
        <= program.YELLOW_PRINTING_THRESHOLD_IN_SECONDS
    ):
        return Back.YELLOW
    if seconds_to_next_duty <= program.RED_PRINTING_THRESHOLD_IN_SECONDS:
        return Back.RED
    if duty.type is DutyType.PROPOSING:
        return Back.GREEN
    return Style.RESET_ALL
