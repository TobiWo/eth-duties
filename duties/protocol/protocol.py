"""Defines ethereum related constants and functions
"""

from math import trunc
from time import time
from protocol.request import send_beacon_api_request
from constants import endpoints, json


def __fetch_genesis_time() -> int:
    """Fetches the genesis time from the beacon client

    Returns:
        int: Genesis time as unix timestamp in seconds
    """
    response = send_beacon_api_request(endpoints.BEACON_GENESIS_ENDPOINT)
    return int(
        response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME][
            json.RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME
        ]
    )


GENESIS_TIME = __fetch_genesis_time()
SLOT_TIME = 12
SLOTS_PER_EPOCH = 32
EPOCHS_PER_SYNC_COMMITTEE = 256


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
