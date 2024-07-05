"""Defines program related constants
"""

from random import randint
from sys import exit
from typing import List


def __create_random_numbers() -> List[int]:
    is_list_filled_with_unique_numbers = False
    cycle_counter = 0
    random_numbers = [0, 0, 0]
    while not is_list_filled_with_unique_numbers and cycle_counter < 1000:
        for index in range(0, 3, 1):
            random_numbers[index] = randint(RANDOM_RANGE_START, RANDOM_RANGE_STOP)
        is_list_filled_with_unique_numbers = len(set(random_numbers)) == len(
            random_numbers
        )
        cycle_counter += 1
    if cycle_counter == 1000:
        exit(
            "Error, could not create unique random numbers for shared memory instances. Please restart eth-duties!"
        )
    return random_numbers


RANDOM_RANGE_START = 1_000_000
RANDOM_RANGE_STOP = 100_000_000
RANDOM_NUMBERS = __create_random_numbers()

REQUEST_TIMEOUT = (3, 5)
REQUEST_CONNECTION_ERROR_WAITING_TIME = 2
REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME = 5
REQUEST_HEADER = {"Content-type": "application/json", "Accept": "application/json"}
DUTY_LOGGING_TIME_FORMAT = "%M:%S"
THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD = 5000
NUMBER_OF_VALIDATORS_PER_REST_CALL = 1000
MAX_NUMBER_OF_VALIDATORS_FOR_FETCHING_ATTESTATION_DUTIES = 100
ALIAS_SEPARATOR = ";"
PUBKEY_PREFIX = "0x"
PUBKEY_LENGTH = 48
SIZE_OF_SHARED_MEMORY = 10_000_000


ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME = (
    f"shared_active_validator_identifiers_with_alias_{RANDOM_NUMBERS[0]}"
)
ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME = (
    f"shared_active_validator_identifiers_{RANDOM_NUMBERS[1]}"
)
UPDATED_SHARED_MEMORY_NAME = f"updated_{RANDOM_NUMBERS[2]}"
ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES = [
    ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME,
    ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME,
]
MINUTES_UNTIL_USED_BEACON_NODE_CONNECTION_STRING_IS_LOGGED_AGAIN = 2
SECONDS_UNTIL_BEACON_NODE_CALL_ERROR_IS_LOGGED_AGAIN = 5
REST_RAW_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT = 7
REST_ANY_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT = 10
HEX_COLOR_STARTING_POSITIONS = (0, 2, 4)
HEX_TO_INT_BASE = 16
USED_STY_BACKGROUND_COLOR_NAMES = ["yellow", "red", "green"]
MANDATORY_NODE_URL_PREFIXES = ("http://", "https://")
