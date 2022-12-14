"""Entrypoint for eth-duties to check for upcoming duties for one or many validators
"""

from time import sleep
from typing import List, Callable
from logging import getLogger, Logger
from fetcher import fetcher
from fetcher.data_types import ValidatorDuty, DutyType
from fetcher.logger import log_time_to_next_duties
from cli.cli import get_arguments
from protocol.protocol import get_current_slot
from constants.program import GRACEFUL_KILLER
from constants import logging

__sort_duties: Callable[[ValidatorDuty], int] = lambda duty: duty.slot


def __fetch_validator_duties(
    duties: List[ValidatorDuty], logger: Logger
) -> List[ValidatorDuty]:
    """Fetches upcoming validator duties

    Args:
        duties (List[ValidatorDuty]): List of validator duties for last logging interval

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    if not __is_current_data_outdated(duties):
        return duties
    next_attestation_duties: dict[int, ValidatorDuty] = {}
    next_sync_committee_duties: dict[int, ValidatorDuty] = {}
    if fetcher.is_provided_validator_count_too_high():
        logger.warning(logging.TOO_MANY_PROVIDED_VALIDATORS_MESSAGE)
    else:
        next_attestation_duties = fetcher.get_next_attestation_duties()
        next_sync_committee_duties = fetcher.get_next_sync_committee_duties()
    next_proposing_duties = fetcher.get_next_proposing_duties()
    duties = [
        duty
        for duties in [
            next_attestation_duties,
            next_proposing_duties,
            next_sync_committee_duties,
        ]
        for duty in duties.values()
    ]
    duties.sort(key=__sort_duties)
    return duties


def __is_current_data_outdated(current_duties: List[ValidatorDuty]) -> bool:
    """Checks if the current fetched validator duties are outdated.

    Args:
        current_duties (List[ValidatorDuty]): Current validator duties fetched during last interval

    Returns:
        bool: True if current data is outdated
    """
    current_slot = get_current_slot()
    first_non_sync_committee_duty = next(
        filter(lambda duty: duty.type is not DutyType.SYNC_COMMITTEE, current_duties),
        None,
    )
    if (
        current_duties
        and first_non_sync_committee_duty
        and first_non_sync_committee_duty.slot > current_slot
    ):
        return False
    return True


if __name__ == "__main__":
    main_logger = getLogger(__name__)
    args = get_arguments()
    upcoming_duties: List[ValidatorDuty] = []
    while not GRACEFUL_KILLER.kill_now:
        upcoming_duties = __fetch_validator_duties(upcoming_duties, main_logger)
        log_time_to_next_duties(upcoming_duties)
        sleep(args.interval)
    main_logger.info("Happy staking. See you for next maintenance \U0001F642 !")
