"""Module with chain related logic
"""

from math import trunc
from time import sleep, time
from typing import Any, List
from urllib.parse import urlencode

# pylint: disable-next=import-error
from constants.program import REQUEST_HEADER, REQUEST_TIMEOUT
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get, post
from test_helper.config import CONFIG

SLOT_TIME = 12
SLOTS_PER_EPOCH = 32


def get_current_epoch() -> int:
    """Calculates the current epoch based on genesis time

    Returns:
        int: Current epoch
    """
    now = time()
    return trunc((now - fetch_genesis_time()) / (SLOTS_PER_EPOCH * SLOT_TIME))


def fetch_genesis_time() -> int:
    """Fetch genesis time from beacon api

    Returns:
        int: Genesis time in seconds
    """
    response = get(
        f"{CONFIG.general.working_beacon_node_url}/eth/v1/beacon/genesis",
        timeout=REQUEST_TIMEOUT,
    )
    return int(response.json()["data"]["genesis_time"])


def get_number_of_active_validators(validators: List[str]) -> int:
    """Fetch number of provided active validators

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        int: Number of provided active validators
    """
    calldata = f"{','.join(validators)}"
    parameters = urlencode({"id": calldata}, safe=",")
    number_of_active_validators = 0
    try_counter = 0
    response = Response()
    while try_counter < 10:
        try:
            try_counter += 1
            response = get(
                url=f"{CONFIG.general.working_beacon_node_url}/eth/v1/beacon/states/head/validators",
                params=parameters,
                timeout=REQUEST_TIMEOUT,
                headers=REQUEST_HEADER,
            )
            for validator in response.json()["data"]:
                if validator["status"] == "active_ongoing":
                    number_of_active_validators += 1
            if response.status_code == 200:
                break
        except (RequestsConnectionError, ReadTimeout):
            sleep(0.1)
    if try_counter == 10:
        raise ValueError("Couldn't fetch data from provided beacon client")
    return number_of_active_validators


def get_number_of_validators_in_current_sync_comittee(validators: List[str]) -> int:
    """Fetch number of provided validators in current sync committee

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        int: Number of provided validators in current sync committee
    """
    validator_request_data = ",".join(f'"{validator}"' for validator in validators)
    validator_request_data = f"[{validator_request_data}]"
    request_string = (
        f"{CONFIG.general.working_beacon_node_url}"
        f"/eth/v1/validator/duties/sync/{get_current_epoch()}"
    )
    try_counter = 0
    response = Response()
    while try_counter < 10:
        try:
            try_counter += 1
            response = post(
                url=request_string,
                data=validator_request_data,
                headers={
                    "Content-type": "application/json",
                    "Accept": "application/json",
                },
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                break
        except (RequestsConnectionError, ReadTimeout):
            sleep(0.1)
    if try_counter == 10:
        raise ValueError("Couldn't fetch data from provided beacon client")
    filtered_response: List[Any] = []
    for item in response.json()["data"]:
        if len(filtered_response) == 0:
            filtered_response.append(item)
        for index, filtered_item in enumerate(filtered_response):
            if item["pubkey"] == filtered_item["pubkey"]:
                break
            if index + 1 == len(filtered_response):
                filtered_response.append(item)
    return len(filtered_response)


def get_number_of_validators_which_will_propose_block(validators: List[str]) -> int:
    """Fetch number of provided validators which will propose a block

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        int: Number of provided validators which will propose a block
    """
    request_strings = [
        (
            f"{CONFIG.general.working_beacon_node_url}"
            f"/eth/v1/validator/duties/proposer/{get_current_epoch() + i}"
        )
        for i in range(0, 2, 1)
    ]
    number_of_validators_which_will_propose_a_block = 0
    response = Response()
    for request in request_strings:
        try_counter = 0
        while try_counter < 10:
            try:
                try_counter += 1
                response = get(url=request, timeout=REQUEST_TIMEOUT)
                for validator_which_will_propose_a_block in response.json()["data"]:
                    if (
                        validator_which_will_propose_a_block["validator_index"]
                        in validators
                    ):
                        number_of_validators_which_will_propose_a_block += 1
                if response.status_code == 200:
                    break
            except (RequestsConnectionError, ReadTimeout):
                sleep(0.1)
        if try_counter == 10:
            raise ValueError("Couldn't fetch data from provided beacon client")
    return number_of_validators_which_will_propose_a_block
