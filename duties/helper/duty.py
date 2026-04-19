"""Duty related helper module
"""

from asyncio import TaskGroup
from multiprocessing.shared_memory import SharedMemory
from typing import List, Sequence, Union

from constants.program import UPDATED_SHARED_MEMORY_NAME
from fetcher.data_types import (
    AttestationDuty,
    ProposingDuty,
    SyncCommitteeDuty,
    ValidatorDuty,
)
from fetcher.fetch import (
    fetch_upcoming_attestation_duties,
    fetch_upcoming_proposing_duties,
    fetch_upcoming_sync_committee_duties,
    update_validator_identifier_cache,
)
from protocol.ethereum import get_current_epoch, get_current_slot, set_time_to_duty


def is_current_data_up_to_date(current_duties: List[ValidatorDuty]) -> bool:
    """Checks if the current fetched validator duties are outdated.

    Args:
        current_duties (List[ValidatorDuty]): Current validator duties fetched during last interval

    Returns:
        bool: True if current data is outdated
    """
    if __has_updated_validator_identifiers():
        return False
    if current_duties:
        duties_up_to_date = [
            __is_first_sync_committee_duty_up_to_date(current_duties),
            __is_first_non_sync_committee_duty_up_to_date(current_duties),
        ]
        if all(duties_up_to_date):
            return True
    return False


def __is_first_non_sync_committee_duty_up_to_date(duties: List[ValidatorDuty]) -> bool:
    """Checks whether the data in memory of the first non sync-committee duty is up to date

    Args:
        duties (List[ValidatorDuty]): Current fetched duties

    Returns:
        bool: Data of first non sync-committee is up to date
    """
    current_slot = get_current_slot()
    first_non_sync_committee_duty: Union[AttestationDuty, ProposingDuty, None] = next(
        (duty for duty in duties if isinstance(duty, (AttestationDuty, ProposingDuty))),
        None,
    )
    if (
        first_non_sync_committee_duty
        and first_non_sync_committee_duty.slot > current_slot
    ):
        return True
    return False


def __is_first_sync_committee_duty_up_to_date(
    duties: List[ValidatorDuty],
) -> bool:
    """Checks whether the data in memory of the first sync-committee duty is up to date

    Args:
        duties (List[ValidatorDuty]): Current fetched duties

    Returns:
        bool: Data of first sync-committee is up to date
    """
    first_duty = duties[0]
    if isinstance(first_duty, SyncCommitteeDuty):
        current_epoch = get_current_epoch()
        if first_duty.epoch >= current_epoch:
            return True
        return False
    return True


def __has_updated_validator_identifiers() -> bool:
    """Checks shared memory instances for updates

    Returns:
        bool: Whether or not shared memory objects got updated
    """
    try:
        identifiers_got_updated = SharedMemory(UPDATED_SHARED_MEMORY_NAME, False)
        update_validator_identifier_cache()
        identifiers_got_updated.close()
        identifiers_got_updated.unlink()
        return True
    except FileNotFoundError:
        pass
    return False


def update_time_to_duty(duties: List[ValidatorDuty]) -> None:
    """Updates the time to duty field via call by reference

    Args:
        duties (List[ValidatorDuty]): Upcoming validator duties
    """
    for duty in duties:
        set_time_to_duty(duty)


async def fetch_upcoming_validator_duties() -> List[ValidatorDuty]:
    """Fetch upcoming validator duties

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    async with TaskGroup() as taskgroup:
        attestation_task = taskgroup.create_task(fetch_upcoming_attestation_duties())
        sync_committee_task = taskgroup.create_task(
            fetch_upcoming_sync_committee_duties()
        )
        proposing_task = taskgroup.create_task(fetch_upcoming_proposing_duties())

    duties: List[ValidatorDuty] = []
    duties.extend(attestation_task.result().values())
    duties.extend(sync_committee_task.result().values())
    duties.extend(proposing_task.result().values())
    duties.sort(key=__sort_duties)
    return duties


def get_duties_proportion_above_time_threshold(
    duties: Sequence[ValidatorDuty], time_threshold: int
) -> float:
    """Get duties proportion above user defined time threshold

    Args:
        duties (Sequence[ValidatorDuty]): List of fetched duties
        time_threshold (int): Time threshold defined by the user

    Returns:
        float: Duties proportion above user defined time threshold
    """
    duties_above_threshold = [
        duty for duty in duties if duty.seconds_to_duty >= time_threshold
    ]
    relevant_duty_proportion = len(duties_above_threshold) / len(duties)
    return relevant_duty_proportion


def __sort_duties(duty: ValidatorDuty) -> int:
    """Sort key for duties - sync committee duties come first, then by slot.

    Args:
        duty (ValidatorDuty): Validator duty

    Returns:
        int: Sort key value
    """
    if isinstance(duty, (AttestationDuty, ProposingDuty)):
        return duty.slot
    return 0
