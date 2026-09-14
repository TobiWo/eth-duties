"""Defines ethereum related constants and functions"""

from asyncio import run
from logging import getLogger
from math import ceil, trunc
from sys import exit as sys_exit
from time import time
from typing import Tuple

from constants import endpoints, json, logging
from fetcher.data_types import SlotBasedDuty, SyncCommitteeDuty, ValidatorDuty
from helper.error import NoDataFromEndpointError
from protocol.request import CalldataType, send_beacon_api_request

__LOGGER = getLogger()


async def __fetch_genesis_time() -> int:
    """Fetches the genesis time from the beacon client

    Returns:
        int: Genesis time as unix timestamp in seconds
    """
    try:
        response = await send_beacon_api_request(
            endpoints.BEACON_GENESIS_ENDPOINT, CalldataType.NONE, flatten=False
        )
        return int(response[0][json.RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME])
    except NoDataFromEndpointError:
        __LOGGER.error(logging.NO_GENESIS_TIME_ERROR_MESSAGE)
        sys_exit(1)


async def __fetch_gloas_fork_epoch() -> int | None:
    """Fetches the Gloas fork epoch from the beacon client

    A beacon node which does not know the Gloas fork is a perfectly valid node.
    In that case ptc duties are not available and will not be fetched.

    Returns:
        int | None: Gloas fork epoch or None if the beacon node does not provide it
    """
    try:
        response = await send_beacon_api_request(
            endpoints.BEACON_SPEC_ENDPOINT, CalldataType.NONE, flatten=False
        )
        gloas_fork_epoch = response[0].get(
            json.RESPONSE_JSON_DATA_GLOAS_FORK_EPOCH_FIELD_NAME
        )
        if gloas_fork_epoch is None:
            __LOGGER.info(logging.NO_GLOAS_FORK_EPOCH_MESSAGE)
            return None
        return int(gloas_fork_epoch)
    except NoDataFromEndpointError:
        __LOGGER.info(logging.NO_GLOAS_FORK_EPOCH_MESSAGE)
        return None


try:
    GENESIS_TIME = run(__fetch_genesis_time())
    GLOAS_FORK_EPOCH = run(__fetch_gloas_fork_epoch())
except KeyboardInterrupt:
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    sys_exit(1)

SLOT_TIME = 12
SLOTS_PER_EPOCH = 32
EPOCHS_PER_SYNC_COMMITTEE = 256
ACTIVE_VALIDATOR_STATUS = ["active_ongoing", "active_exiting", "active_slashed"]


def get_current_slot() -> int:
    """Calculates the current beacon chain slot

    Returns:
        int: The current beacon chain slot
    """
    return trunc((time() - GENESIS_TIME) / SLOT_TIME)


def get_current_epoch() -> int:
    """Calculates the current beacon chain epoch

    Returns:
        int: Current epoch
    """
    now = time()
    return trunc((now - GENESIS_TIME) / (SLOTS_PER_EPOCH * SLOT_TIME))


def is_gloas_active() -> bool:
    """Checks whether the Gloas fork is active on the connected chain

    The fork schedule is fetched once during startup while the activation itself
    is checked on every call. This way ptc duties are picked up automatically as
    soon as the fork epoch is reached.

    Returns:
        bool: Whether or not the Gloas fork is active
    """
    if GLOAS_FORK_EPOCH is None:
        return False
    return get_current_epoch() >= GLOAS_FORK_EPOCH


def set_time_to_duty(duty: ValidatorDuty) -> None:
    """Sets the time (in seconds) until the provided duty is due, via call by reference

    Args:
        duty (ValidatorDuty): Validator duty
    """
    if isinstance(duty, SyncCommitteeDuty):
        current_slot = get_current_slot()
        current_epoch = get_current_epoch()
        current_sync_committee_epoch_boundaries = get_sync_committee_epoch_boundaries(
            current_epoch
        )
        time_to_next_sync_committee = get_time_to_next_sync_committee(
            current_sync_committee_epoch_boundaries, current_slot
        )
        if duty.epoch in range(
            current_sync_committee_epoch_boundaries[0],
            current_sync_committee_epoch_boundaries[1] + 1,
            1,
        ):
            duty.seconds_to_duty = 0
            duty.seconds_left_in_current_sync_committee = (
                time_to_next_sync_committee - 1
            )
        else:
            duty.seconds_to_duty = time_to_next_sync_committee
    elif isinstance(duty, SlotBasedDuty):
        duty.seconds_to_duty = int(duty.slot * SLOT_TIME + GENESIS_TIME - time())


def get_time_to_next_sync_committee(
    sync_committee_boundaries: Tuple[int, int], current_slot: int
) -> int:
    """Gets the remaining time (in seconds) until next sync committee starts

    Args:
        sync_committee_boundaries (Tuple[int, int]): Lower and Upper epoch boundaries for provided sync committee # pylint: disable=line-too-long
        current_slot (int): The current slot

    Returns:
        int: Time (in seconds) until next sync committee starts
    """
    next_sync_committee_starting_slot = SLOTS_PER_EPOCH * (
        sync_committee_boundaries[1] + 1
    )
    number_of_slots_to_next_sync_committee = (
        next_sync_committee_starting_slot - current_slot
    )
    return number_of_slots_to_next_sync_committee * SLOT_TIME


def get_sync_committee_epoch_boundaries(epoch: int) -> Tuple[int, int]:
    """Gets sync committee lower and upper epoch boundaries based on the provided epoch

    Args:
        epoch (int): Provided epoch

    Returns:
        Tuple[int, int]: Lower and upper sync committee epoch boundaries
    """
    current_sync_committee_epoch_lower_bound: int = (
        trunc(epoch / EPOCHS_PER_SYNC_COMMITTEE) * EPOCHS_PER_SYNC_COMMITTEE
    )
    current_sync_committee_epoch_upper_bound: int = (
        ceil(epoch / EPOCHS_PER_SYNC_COMMITTEE) * EPOCHS_PER_SYNC_COMMITTEE
    ) - 1
    return (
        current_sync_committee_epoch_lower_bound,
        current_sync_committee_epoch_upper_bound,
    )
