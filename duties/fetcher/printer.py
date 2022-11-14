"""
Module for printing validator duties
"""

# pylint: disable=import-error

from time import time, strftime, gmtime
from typing import List
from colorama import Back, Style
from .data_types import ValidatorDuty, DutyType
from .constants import (
    NEXT_INTERVAL_MESSAGE,
    SLOT_TIME,
    PRINTER_TIME_FORMAT,
    NO_UPCOMING_DUTIES_MESSAGE,
    RED_PRINTING_THRESHOLD_IN_SECONDS,
    YELLOW_PRINTING_THRESHOLD_IN_SECONDS,
)


def print_time_to_next_duties(
    validator_duties: List[ValidatorDuty], genesis_time: int
) -> None:
    """Prints time to next duties for the provided validators

    Args:
        validator_duties (List[ValidatorDuty]): List of validator duties
        genesis_time (int): Genesis time of the connected chain
    """
    print(NEXT_INTERVAL_MESSAGE)
    if validator_duties:
        for duty in validator_duties:
            now = time()
            seconds_to_next_duty = duty.slot * SLOT_TIME + genesis_time - now
            if seconds_to_next_duty < 0:
                print(
                    f"Upcoming {duty.type.name} duty "
                    f"for validator {duty.validator_index} outdated. "
                    f"Fetching duties in next interval."
                )
            else:
                time_to_next_duty = strftime(
                    PRINTER_TIME_FORMAT, gmtime(float(seconds_to_next_duty))
                )
                print(
                    f"{__get_printing_color(seconds_to_next_duty, duty)}"
                    f"Validator {duty.validator_index} has next {duty.type.name} duty in: "
                    f"{time_to_next_duty} min. (slot: {duty.slot}){Style.RESET_ALL}"
                )
    else:
        print(NO_UPCOMING_DUTIES_MESSAGE)


def __get_printing_color(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    if (
        RED_PRINTING_THRESHOLD_IN_SECONDS
        < seconds_to_next_duty
        <= YELLOW_PRINTING_THRESHOLD_IN_SECONDS
    ):
        return Back.YELLOW
    if seconds_to_next_duty <= RED_PRINTING_THRESHOLD_IN_SECONDS:
        return Back.RED
    if duty.type is DutyType.PROPOSING:
        return Back.GREEN
    return Style.RESET_ALL
