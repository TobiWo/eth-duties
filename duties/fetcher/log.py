"""Module for logging validator duties
"""

from datetime import timedelta
from logging import getLogger
from time import gmtime, strftime
from typing import List, Tuple

from cli.arguments import ARGUMENTS
from constants import logging, program
from fetcher.data_types import DutyType, ValidatorDuty, ValidatorIdentifier
from fetcher.identifier.core import read_validator_identifiers_from_shared_memory
from helper.help import (
    format_timedelta_to_hours,
    get_duties_proportion_above_time_threshold,
)
from protocol import ethereum
from sty import bg, rs  # type: ignore[import]

__validator_identifiers_with_alias = {"0": ValidatorIdentifier()}

__LOGGER = getLogger()


def log_time_to_next_duties(validator_duties: List[ValidatorDuty]) -> None:
    """Logs the time to next duties for the provided validators to the console

    Args:
        validator_duties (List[ValidatorDuty]): List of validator duties
    """
    __set_global_validator_identifiers_with_alias()
    print("")
    __LOGGER.info(logging.NEXT_INTERVAL_MESSAGE)
    if validator_duties:
        for duty in validator_duties:
            logging_message = __create_logging_message(duty)
            __LOGGER.info(logging_message)
        __log_duty_proportion_above_time_threshold(validator_duties)
    else:
        __LOGGER.info(logging.NO_UPCOMING_DUTIES_MESSAGE)


def __set_global_validator_identifiers_with_alias() -> None:
    """Sets the validator identifiers with alias"""
    # pylint: disable-next=invalid-name, global-statement
    global __validator_identifiers_with_alias
    __validator_identifiers_with_alias = read_validator_identifiers_from_shared_memory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME
    )


def __log_duty_proportion_above_time_threshold(
    validator_duties: List[ValidatorDuty],
) -> None:
    """Log the proportion of validator duties above a defined time threshold

    Args:
        validator_duties (List[ValidatorDuty]): List of validator duties
    """
    relevant_duty_proportion = get_duties_proportion_above_time_threshold(
        validator_duties, ARGUMENTS.log_time_warning
    )
    __LOGGER.info(
        logging.PROPORTION_OF_DUTIES_ABOVE_TIME_THRESHOLD_MESSAGE,
        round(relevant_duty_proportion * 100, 2),
        "all",
        ARGUMENTS.log_time_warning,
    )


def __create_logging_message(duty: ValidatorDuty) -> str:
    """Creates the logging message for the provided duty

    Args:
        seconds_to_next_duty (float): Time to next duty in seconds
        duty (ValidatorDuty): Specific upcoming validator duty

    Returns:
        str: Message which will be logged to stdout
    """
    if duty.type is DutyType.SYNC_COMMITTEE:
        logging_message = __create_sync_committee_logging_message(duty)
    elif duty.seconds_to_duty < 0:
        logging_message = (
            f"Upcoming {duty.type.name} duty "
            f"for validator {__get_validator_identifier_for_logging(duty)} outdated. "
            f"Fetching duties in next interval."
        )
    else:
        time_to_next_duty = strftime(
            program.DUTY_LOGGING_TIME_FORMAT,
            gmtime(duty.seconds_to_duty),
        )
        logging_message = (
            f"{__get_logging_color(duty.seconds_to_duty, duty)}"
            f"Validator {__get_validator_identifier_for_logging(duty)} "
            f"has next {duty.type.name} duty in: "
            f"{time_to_next_duty} min. (slot: {duty.slot}){rs.all}"
        )
    return logging_message


def __create_sync_committee_logging_message(sync_committee_duty: ValidatorDuty) -> str:
    """Create a sync committee duty related logging message

    Args:
        duty (ValidatorDuty): Sync committee duty

    Returns:
        str: sync committee duty related logging message
    """
    current_epoch = ethereum.get_current_epoch()
    current_sync_committee_epoch_boundaries = (
        ethereum.get_sync_committee_epoch_boundaries(current_epoch)
    )
    time_to_next_sync_committee = format_timedelta_to_hours(
        __get_time_to_next_sync_committee(
            sync_committee_duty, current_sync_committee_epoch_boundaries
        )
    )
    if sync_committee_duty.seconds_to_duty == 0:
        logging_message = (
            f"{bg.red}Validator {__get_validator_identifier_for_logging(sync_committee_duty)} "
            f"is in current sync committee (next sync committee starts in "
            f"{time_to_next_sync_committee} / "
            f"epoch: {current_sync_committee_epoch_boundaries[1] + 1}){rs.all}"
        )
    else:
        logging_message = (
            f"{bg.yellow}Validator "
            f"{__get_validator_identifier_for_logging(sync_committee_duty)} will be in next "
            f"sync committee which starts in {time_to_next_sync_committee} "
            f"(epoch: {current_sync_committee_epoch_boundaries[1] + 1}){rs.all}"
        )
    return logging_message


def __get_time_to_next_sync_committee(
    sync_committee_duty: ValidatorDuty,
    current_sync_committee_epoch_boundaries: Tuple[int, int],
) -> timedelta:
    """Get the time when next sync committee starts

    Args:
        sync_committee_duty (ValidatorDuty): Sync committee duty
        current_sync_committee_epoch_boundaries (Tuple[int, int]): Lower and Upper epoch boundaries
        for current sync committee

    Returns:
        str: Time to next sync committee start
    """
    if sync_committee_duty.seconds_to_duty > 0:
        return timedelta(seconds=sync_committee_duty.seconds_to_duty)
    current_slot = ethereum.get_current_slot()
    return timedelta(
        seconds=ethereum.get_time_to_next_sync_committee(
            current_sync_committee_epoch_boundaries, current_slot
        )
    )


def __get_logging_color(seconds_to_next_duty: float, duty: ValidatorDuty) -> str:
    """Gets correct logging color in dependence of duty and time to next duty

    Args:
        seconds_to_next_duty (float): Time to next duty in seconds
        duty (ValidatorDuty): Specific upcoming validator duty

    Returns:
        str: ANSI codes for colorful logging
    """
    if ARGUMENTS.log_time_critical < seconds_to_next_duty <= ARGUMENTS.log_time_warning:
        return bg.yellow
    if seconds_to_next_duty <= ARGUMENTS.log_time_critical:
        return bg.red
    if duty.type is DutyType.PROPOSING:
        return bg.green
    return rs.all


def __get_validator_identifier_for_logging(duty: ValidatorDuty) -> str:
    """Gets the validator identifier for logging

    Args:
        duty (ValidatorDuty): Validator duty

    Returns:
        str: Validator identifier
    """
    alias = __get_alias(duty)
    if alias:
        return alias
    if ARGUMENTS.log_pubkeys:
        return duty.pubkey
    return duty.validator_index


def __get_alias(duty: ValidatorDuty) -> str | None:
    """Gets the validator alias

    Args:
        duty (ValidatorDuty): Validator duty

    Returns:
        str | None: Validator alias
    """
    validator_with_alias = __validator_identifiers_with_alias.get(duty.validator_index)
    if validator_with_alias and validator_with_alias.alias:
        return validator_with_alias.alias
    return None
