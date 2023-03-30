"""Entrypoint for eth-duties to check for upcoming duties for one or many validators
"""

from logging import getLogger
from time import sleep
from typing import Callable, List

from cli.arguments import ARGUMENTS
from constants.program import GRACEFUL_TERMINATOR
from fetcher import fetch
from fetcher.data_types import DutyType, ValidatorDuty
from fetcher.log import log_time_to_next_duties
from protocol.ethereum import get_current_slot

__sort_duties: Callable[[ValidatorDuty], int] = lambda duty: duty.slot


def __fetch_validator_duties(
    duties: List[ValidatorDuty],
) -> List[ValidatorDuty]:
    """Fetches upcoming validator duties

    Args:
        duties (List[ValidatorDuty]): List of validator duties for last logging interval

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    if not __is_current_data_outdated(duties):
        return duties
    next_attestation_duties = fetch.get_next_attestation_duties()
    next_sync_committee_duties = fetch.get_next_sync_committee_duties()
    next_proposing_duties = fetch.get_next_proposing_duties()
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
    upcoming_duties: List[ValidatorDuty] = []
    while not GRACEFUL_TERMINATOR.kill_now:
        upcoming_duties = __fetch_validator_duties(upcoming_duties)
        log_time_to_next_duties(upcoming_duties)
        GRACEFUL_TERMINATOR.terminate_in_cicd_mode(ARGUMENTS.mode, upcoming_duties)
        sleep(ARGUMENTS.interval)
    main_logger.info("Happy staking. See you for next maintenance \U0001F642 !")
