"""Defines program related constants"""

from os import environ
from random import randint
from sys import exit as sys_exit
from typing import List


def __get_shared_memory_ids() -> List[int]:
    """Returns the shared memory ids of this eth-duties instance

    Child processes (e.g. the rest server) inherit the ids of their parent process via
    an environment variable. The parent process creates new random ids.

    Returns:
        List[int]: Shared memory ids
    """
    if IS_SHARED_MEMORY_OWNER:
        return __create_random_numbers()
    return [
        int(shared_memory_id)
        for shared_memory_id in environ[SHARED_MEMORY_IDS_ENVIRONMENT_VARIABLE].split(
            SHARED_MEMORY_IDS_SEPARATOR
        )
    ]


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
        sys_exit(
            "Error, could not create unique random numbers for shared memory instances. "
            "Please restart eth-duties!"
        )
    return random_numbers


# Shared memory id creation
RANDOM_RANGE_START = 1_000_000
RANDOM_RANGE_STOP = 100_000_000
SHARED_MEMORY_IDS_ENVIRONMENT_VARIABLE = "ETH_DUTIES_SHARED_MEMORY_IDS"
SHARED_MEMORY_IDS_SEPARATOR = ","
IS_SHARED_MEMORY_OWNER = SHARED_MEMORY_IDS_ENVIRONMENT_VARIABLE not in environ
RANDOM_NUMBERS = __get_shared_memory_ids()

# General program settings
REQUEST_TIMEOUT = (3, 5)
REQUEST_CONNECTION_ERROR_WAITING_TIME = 2
REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME = 5
REQUEST_HEADER = {"Content-type": "application/json", "Accept": "application/json"}
DUTY_LOGGING_TIME_FORMAT = "%M:%S"
THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD = 5000
NUMBER_OF_VALIDATORS_PER_REST_CALL = 1000
MAX_GET_URL_IDS_BYTES = 6400
MAX_NUMBER_OF_VALIDATORS_FOR_FETCHING_ATTESTATION_DUTIES = 100
ALIAS_SEPARATOR = ";"
PUBKEY_PREFIX = "0x"
PUBKEY_LENGTH = 48
MANDATORY_NODE_URL_PREFIXES = ("http://", "https://")
VALIDATOR_HEALTH_UPDATE_INTERVAL = 60

# Shared memory settings
SIZE_OF_SHARED_MEMORY = 10_000_000
ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME = (
    f"val_alias_{RANDOM_NUMBERS[0]}"
)
ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME = f"val_ids_{RANDOM_NUMBERS[1]}"
UPDATED_SHARED_MEMORY_NAME = f"updated_{RANDOM_NUMBERS[2]}"
ALL_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAMES = [
    ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME,
    ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME,
]

# Beacon node logging and health
MINUTES_UNTIL_USED_BEACON_NODE_CONNECTION_STRING_IS_LOGGED = 1
MINUTES_UNTIL_ALL_HEALTHY_BEACON_NODE_CONNECTION_STRINGS_ARE_LOGGED = 1
SECONDS_UNTIL_BEACON_NODE_HEALTH_UPDATE = 7

# REST specific settings
REST_RAW_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT = 7
REST_ANY_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT = 10

# sty specific settings
HEX_COLOR_STARTING_POSITIONS = (0, 2, 4)
HEX_TO_INT_BASE = 16
USED_STY_BACKGROUND_COLOR_NAMES = ["yellow", "red", "green"]
