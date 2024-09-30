"""Entrypoint for eth-duties to check for upcoming duties for one or many validators
"""

from asyncio import CancelledError, TaskGroup, run, sleep
from logging import Logger, getLogger
from math import floor
from platform import system
from typing import List

from cli.arguments import ARGUMENTS
from cli.types import Mode
from constants import logging
from fetcher.data_types import ValidatorDuty
from fetcher.identifier.parser import (
    update_shared_active_validator_identifiers_on_interval,
)
from fetcher.log import log_time_to_next_duties
from helper.duty import (
    fetch_upcoming_validator_duties,
    is_current_data_up_to_date,
    update_time_to_duty,
)
from helper.identifier import clean_shared_memory
from helper.terminate import GracefulTerminator
from protocol.connection import BeaconNode
from protocol.request import validator_node
from rest.app import create_rest_server
from rest.core.server import RestServer

__LOGGER = getLogger()
beacon_node = BeaconNode()


async def __fetch_validator_duties(
    duties: List[ValidatorDuty],
) -> List[ValidatorDuty]:
    """Fetches upcoming validator duties

    Args:
        duties (List[ValidatorDuty]): List of validator duties for last logging interval

    Returns:
        List[ValidatorDuty]: Sorted list with all upcoming validator duties
    """
    if is_current_data_up_to_date(duties):
        __check_beacon_node_connection()
        return duties
    return await fetch_upcoming_validator_duties()


def __check_beacon_node_connection() -> None:
    """Check healthiness of beacon node connections while using cached data"""
    beacon_node.get_healthy_beacon_node(True)
    if not beacon_node.is_any_node_healthy:
        __LOGGER.warning(
            "Cached data will only be used until next upcoming duty is due"
        )


async def __main() -> None:
    async with TaskGroup() as taskgroup:
        taskgroup.create_task(__main_process())
        taskgroup.create_task(update_shared_active_validator_identifiers_on_interval())
        taskgroup.create_task(validator_node.update_validator_node_health())


async def __main_process() -> None:
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
            update_time_to_duty(upcoming_duties)
            log_time_to_next_duties(upcoming_duties)
            graceful_terminator.terminate_in_cicd_mode(upcoming_duties)
            await sleep(ARGUMENTS.interval)
        else:
            await sleep(ARGUMENTS.interval)


def __start_processes(rest_server: RestServer, logger: Logger) -> None:
    """Starts the relevant processes

    Args:
        rest_server (RestServer): Rest server object
        logger (Logger): Logger instance
    """
    if ARGUMENTS.rest and not "cicd" in ARGUMENTS.mode.value:
        rest_server.start()
        rest_server.server.started = True
        run(__main())
    elif ARGUMENTS.rest and "cicd" in ARGUMENTS.mode.value:
        logger.info(logging.IGNORED_REST_FLAG_MESSAGE)
        run(__main())
    else:
        run(__main())


if __name__ == "__main__":
    main_logger = getLogger()
    main_logger.info(logging.ACTIVATED_MODE_MESSAGE, ARGUMENTS.mode.value)
    rest_api_server = create_rest_server()
    try:
        __start_processes(rest_api_server, main_logger)
    except (CancelledError, KeyboardInterrupt):
        if rest_api_server.server.started:
            rest_api_server.stop()
        clean_shared_memory()
        main_logger.error(logging.SYSTEM_EXIT_MESSAGE)
    main_logger.info(logging.MAIN_EXIT_MESSAGE)
