"""Entrypoint for eth-duties to check for upcoming duties for one or many validators
"""

from asyncio import CancelledError, run, sleep
from logging import getLogger
from math import floor
from platform import system
from typing import List

from cli.arguments import ARGUMENTS
from cli.types import Mode
from constants import logging
from fetcher import fetch
from fetcher.data_types import ValidatorDuty
from fetcher.log import log_time_to_next_duties
from helper import help
from helper.terminate import GracefulTerminator
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
    if help.is_current_data_up_to_date(duties):
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
    duties.sort(key=help.sort_duties)
    return duties


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
            help.update_time_to_duty(upcoming_duties)
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
        help.clean_shared_memory()
        main_logger.error(logging.SYSTEM_EXIT_MESSAGE)
    main_logger.info(logging.MAIN_EXIT_MESSAGE)
