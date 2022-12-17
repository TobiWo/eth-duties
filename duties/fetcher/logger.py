"""Module for logging validator duties
"""

from time import time, strftime, gmtime
from logging import getLogger
from typing import List
from math import ceil, trunc
from colorama import Back, Style
from fetcher.data_types import ValidatorDuty, DutyType
from constants import logging, program
from protocol import protocol


def log_time_to_next_duties(validator_duties: List[ValidatorDuty]) -> None:
    """Logs the time to next duties for the provided validators to the console

    Args:
        validator_duties (List[ValidatorDuty]): List of validator duties
    """
    logger = getLogger(__name__)
    logger.info(logging.NEXT_INTERVAL_MESSAGE)
    if validator_duties:
        for index, duty in enumerate(validator_duties):
            now = time()
            seconds_to_next_duty = (
                duty.slot * protocol.SLOT_TIME + protocol.GENESIS_TIME - now
            )
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
    if duty.type is DutyType.SYNC_COMMITTEE:
        logging_message = __create_sync_committee_logging_message(duty)
    elif seconds_to_next_duty < 0:
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
            f"{__get_logging_color(seconds_to_next_duty, duty)}"
            f"Validator {duty.validator_index} has next {duty.type.name} duty in: "
            f"{time_to_next_duty} min. (slot: {duty.slot}){Style.RESET_ALL}"
        )
    return logging_message


def __create_sync_committee_logging_message(duty: ValidatorDuty) -> str:
    """Create a sync committee duty related logging message

    Args:
        duty (ValidatorDuty): Sync committee duty

    Returns:
        str: sync committee duty related logging message
    """
    current_epoch = protocol.get_current_epoch()
    current_sync_committee_epoch_lower_bound: int = (
        trunc(current_epoch / protocol.EPOCHS_PER_SYNC_COMMITTEE)
        * protocol.EPOCHS_PER_SYNC_COMMITTEE
    )
    current_sync_committee_epoch_upper_bound: int = (
        ceil(current_epoch / protocol.EPOCHS_PER_SYNC_COMMITTEE)
        * protocol.EPOCHS_PER_SYNC_COMMITTEE
    ) - 1
    if duty.epoch in range(
        current_sync_committee_epoch_lower_bound,
        current_sync_committee_epoch_upper_bound + 1,
        1,
    ):
        logging_message = (
            f"{Back.RED}Validator {duty.validator_index} is in current sync committee "
            f"(next sync committee starts at epoch "
            f"{current_sync_committee_epoch_upper_bound + 1}){Style.RESET_ALL}"
        )
    else:
        logging_message = (
            f"{Back.YELLOW}Validator {duty.validator_index} will be in sync committee "
            f"starting at epoch {current_sync_committee_epoch_upper_bound + 1}{Style.RESET_ALL}"
        )
    return logging_message


def __get_logging_color(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    """Gets correct logging color in dependence of duty and time to next duty

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
