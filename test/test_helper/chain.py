"""Module with chain related logic"""

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


def __post_duties_request(endpoint: str, validators: List[str]) -> Response:
    """Post a duties request with a validator identifier body to the beacon api

    Args:
        endpoint: Duty endpoint including the target epoch
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        Response: Response object provided by the beacon api
    """
    validator_request_data = ",".join(f'"{validator}"' for validator in validators)
    validator_request_data = f"[{validator_request_data}]"
    try_counter = 0
    response = Response()
    while try_counter < 10:
        try:
            try_counter += 1
            response = post(
                url=f"{CONFIG.general.working_beacon_node_url}{endpoint}",
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
    return response


def get_number_of_validators_in_current_sync_comittee(validators: List[str]) -> int:
    """Fetch number of provided validators in current sync committee

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        int: Number of provided validators in current sync committee
    """
    response = __post_duties_request(
        f"/eth/v1/validator/duties/sync/{get_current_epoch()}", validators
    )
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


def get_number_of_validators_in_ptc(validators: List[str]) -> int:
    """Fetch number of provided validators which are assigned to the payload
    timeliness committee for the current or next epoch

    Ptc committees are drawn per epoch. The app fetches ahead into the next
    epoch for any validator whose current-epoch slot based duty is already
    outdated, so both epochs need to be checked here to get a matching count.

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        int: Number of provided validators assigned to the ptc
    """
    current_epoch = get_current_epoch()
    ptc_indices = set(__fetch_ptc_validator_indices(current_epoch, validators))
    ptc_indices.update(__fetch_ptc_validator_indices(current_epoch + 1, validators))
    return len(ptc_indices)


def get_validators_with_ptc_duty(validators: List[str]) -> List[str]:
    """Fetch provided validators which are assigned to the payload timeliness committee

    Ptc membership is redrawn every epoch which is why this has to be resolved
    while a test is running instead of during test config preparation. On a small
    devnet a ptc member will almost always also have an attestation duty in the
    same slot, so exclusivity is not required here; tests isolate the ptc log
    line via '--omit-attestation-duties' / '--omit-sync-committee-duties' instead.

    Args:
        validators (List[str]): Validator identifiers

    Raises:
        ValueError: Could not fetch data from beacon client

    Returns:
        List[str]: Validator identifiers with an upcoming ptc duty
    """
    return __fetch_ptc_validator_indices(get_current_epoch(), validators)


def __fetch_ptc_validator_indices(epoch: int, validators: List[str]) -> List[str]:
    """Fetch validator indices with a ptc duty for the provided epoch

    Args:
        epoch (int): Epoch to fetch ptc duties for
        validators (List[str]): Validator identifiers

    Returns:
        List[str]: Validator indices with an upcoming ptc duty
    """
    response = __post_duties_request(
        f"/eth/v1/validator/duties/ptc/{epoch}", validators
    )
    return list(
        dict.fromkeys(duty["validator_index"] for duty in response.json()["data"])
    )


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
            f"/eth/v2/validator/duties/proposer/{get_current_epoch() + i}"
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
