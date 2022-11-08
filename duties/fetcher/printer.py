"""
Module for printing validator duties
"""

from time import time, strftime, gmtime
from colorama import Back, Style
from typing import List
from .data_types import ValidatorDuty, DutyType

YELLOW_PRINTING_THRESHOLD = 120.0
RED_PRINTING_THRESHOLD = 60.0


def print_time_to_next_duties(
    validator_duties: List[ValidatorDuty], genesis_time: int
) -> None:
    print("\nPrinting next interval...")
    if validator_duties:
        for duty in validator_duties:
            now = time()
            seconds_to_next_duty = (
                duty.target_slot * 12 + genesis_time - now  # +4 nimbus / +0 teku?
            )
            if seconds_to_next_duty < 0:
                print(
                    f"Upcoming {duty.type.name} duty "
                    f"for validator {duty.validator_index} outdated. "
                    f"Fetching duties in next interval."
                )
            else:
                time_to_next_duty = strftime(
                    "%M:%S", gmtime(float(seconds_to_next_duty))
                )
                print(
                    f"{__get_printing_color(seconds_to_next_duty, duty)}"
                    f"Validator {duty.validator_index} has next {duty.type.name} duty in: "
                    f"{time_to_next_duty} min. (slot: {duty.target_slot}){Style.RESET_ALL}"
                )
    else:
        print("No upcoming duties detected!")


def __get_printing_color(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    if RED_PRINTING_THRESHOLD < seconds_to_next_duty <= YELLOW_PRINTING_THRESHOLD:
        return Back.YELLOW
    if seconds_to_next_duty <= RED_PRINTING_THRESHOLD:
        return Back.RED
    if duty.type is DutyType.PROPOSING:
        return Back.GREEN
    return Style.RESET_ALL
