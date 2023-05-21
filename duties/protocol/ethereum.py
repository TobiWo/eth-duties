"""Defines ethereum related constants and functions
"""
from asyncio import run
from logging import getLogger
from math import trunc
from sys import exit as sys_exit
from time import time

from constants import endpoints, json, logging
from protocol.request import CalldataType, send_beacon_api_request

__LOGGER = getLogger()


async def __fetch_genesis_time() -> int:
    """Fetches the genesis time from the beacon client

    Returns:
        int: Genesis time as unix timestamp in seconds
    """
    response = await send_beacon_api_request(
        endpoints.BEACON_GENESIS_ENDPOINT, CalldataType.NONE, flatten=False
    )
    return int(response[0][json.RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME])


try:
    GENESIS_TIME = run(__fetch_genesis_time())
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
