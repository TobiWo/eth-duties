"""Entrypoint for eth-duties to check for upcoming duties for one or many validators
"""

from asyncio import CancelledError, run, sleep
from logging import getLogger
from math import floor
from multiprocessing.shared_memory import SharedMemory
from platform import system
from typing import List

from cli.arguments import ARGUMENTS
from cli.types import Mode
from constants import logging, program
from fetcher import fetch
from fetcher.data_types import DutyType, ValidatorDuty
from fetcher.fetch import update_validator_identifiers
from fetcher.log import log_time_to_next_duties
from helper.help import sort_duties
from helper.terminate import GracefulTerminator
from protocol import ethereum
from protocol.ethereum import get_current_slot
from rest.app import start_rest_server


async def __fetch_validator_duties(
    duties: List[ValidatorDuty],
) -> List[ValidatorDuty]:
    """Fetches upcoming validator duties

    Args:
        duties (List[ValidatorDuty]): List of validator duties for last logging interval

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    if not await __is_current_data_outdated(duties):
        return duties
    next_attestation_duties = await fetch.get_next_attestation_duties()
    next_sync_committee_duties = await fetch.get_next_sync_committee_duties()
    next_proposing_duties = await fetch.get_next_proposing_duties()
    duties = [
        duty
        for duties in [
            next_attestation_duties,
            next_proposing_duties,
            next_sync_committee_duties,
        ]
        for duty in duties.values()
    ]
    duties.sort(key=sort_duties)
    return duties


async def __is_current_data_outdated(current_duties: List[ValidatorDuty]) -> bool:
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
    if __has_updated_validator_identifiers():
        return True
    if (
        current_duties
        and first_non_sync_committee_duty
        and first_non_sync_committee_duty.slot > current_slot
    ):
        return False
    return True


def __has_updated_validator_identifiers() -> bool:
    """Checks shared memory instances for updates

    Returns:
        bool: Whether or not shared memory objects got updated
    """
    try:
        identifiers_got_updated = SharedMemory("updated", False)
        update_validator_identifiers()
        identifiers_got_updated.close()
        identifiers_got_updated.unlink()
        return True
    except FileNotFoundError:
        pass
    return False


def __update_time_to_duty(duties: List[ValidatorDuty]) -> None:
    """Updates the time to duty field via call by reference

    Args:
        duties (List[ValidatorDuty]): Upcoming validator duties
    """
    for duty in duties:
        ethereum.set_time_to_duty(duty)


def __clean_shared_memory() -> None:
    """Releases shared memory instances"""
    for (
        validator_identifier_shared_memory_name
    ) in program.ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES:
        shared_memory_validator_identifiers = SharedMemory(
            validator_identifier_shared_memory_name, False
        )
        shared_memory_validator_identifiers.close()
        shared_memory_validator_identifiers.unlink()


async def main() -> None:
    """eth-duties main function"""
    graceful_terminator = GracefulTerminator(
        floor(ARGUMENTS.mode_cicd_waiting_time / ARGUMENTS.interval)
    )
    if system() != "Windows":
        await graceful_terminator.create_signal_handlers()
    upcoming_duties: List[ValidatorDuty] = []
    while True:
        if ARGUMENTS.mode != Mode.NO_LOG:
            upcoming_duties = await __fetch_validator_duties(upcoming_duties)
            __update_time_to_duty(upcoming_duties)
            log_time_to_next_duties(upcoming_duties)
            graceful_terminator.terminate_in_cicd_mode(upcoming_duties)
            await sleep(ARGUMENTS.interval)
        else:
            await sleep(ARGUMENTS.interval)


if __name__ == "__main__":
    main_logger = getLogger(__name__)
    main_logger.info(logging.ACTIVATED_MODE_MESSAGE, ARGUMENTS.mode.value)
    try:
        if ARGUMENTS.rest:
            start_rest_server()
            run(main())
        else:
            run(main())
    except (CancelledError, KeyboardInterrupt) as exception:
        __clean_shared_memory()
        main_logger.error(logging.SYSTEM_EXIT_MESSAGE)
    main_logger.info(logging.MAIN_EXIT_MESSAGE)
