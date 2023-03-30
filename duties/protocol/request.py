"""Module for fetching data from a beacon client
"""

from enum import Enum
from itertools import chain
from logging import getLogger
from time import sleep
from typing import Any, List

from cli.arguments import ARGUMENTS
from constants import json, logging, program
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get, post

__LOGGER = getLogger(__name__)


class CalldataType(Enum):
    """Defines the type of the calldata for the rest call"""

    NONE = 0
    REQUEST_DATA = 1
    PARAMETERS = 2


def send_beacon_api_request(
    endpoint: str,
    calldata_type: CalldataType,
    provided_validators: List[str] | None = None,
    flatten: bool = True,
) -> List[Any]:
    """Sends api requests to the beacon client and returns the subsequent data objects
    from the responses

    Args:
        endpoint (str): The endpoint which will be called
        calldata_type (CalldataType): The type of calldata submitted with the request
        provided_validators (List[str]): The validator indices or pubkey to get information for
        flatten (bool): If True the returned list will be flattened

    Returns:
        List[Any]: List with data objects from responses
    """

    responses: List[Response] = []
    if provided_validators:
        chunked_validators = [
            provided_validators[
                index : index + program.NUMBER_OF_VALIDATORS_PER_REST_CALL
            ]
            for index in range(
                0, len(provided_validators), program.NUMBER_OF_VALIDATORS_PER_REST_CALL
            )
        ]
        for chunk in chunked_validators:
            responses.append(__send_request(endpoint, calldata_type, chunk))
    else:
        responses.append(__send_request(endpoint, calldata_type, []))
    return __convert_to_raw_data_responses(responses, flatten)


def __send_request(
    endpoint: str,
    calldata_type: CalldataType,
    provided_validators: List[str],
) -> Response:
    """Sends a single request to the beacon client

    Args:
        endpoint (str): The endpoint which will be called
        calldata_type (CalldataType): The type of calldata submitted with the request
        provided_validators (List[str]): The validator indices or pubkey to get information for

    Raises:
        SystemExit: Program exit if the response is not present at all
        which will happen if the user interrupts at specific moment during
        execution

    Returns:
        Response: Response object with data provided by the endpoint
    """
    is_request_successful = False
    response = None
    calldata = __get_processed_calldata(provided_validators, calldata_type)
    while not is_request_successful and not program.GRACEFUL_TERMINATOR.kill_now:
        try:
            match calldata_type:
                case CalldataType.REQUEST_DATA:
                    response = post(
                        url=f"{ARGUMENTS.beacon_node}{endpoint}",
                        data=calldata,
                        timeout=program.REQUEST_TIMEOUT,
                    )
                case CalldataType.PARAMETERS:
                    response = get(
                        url=f"{ARGUMENTS.beacon_node}{endpoint}",
                        params={"id": calldata},
                        timeout=program.REQUEST_TIMEOUT,
                    )
                case _:
                    response = get(
                        url=f"{ARGUMENTS.beacon_node}{endpoint}",
                        timeout=program.REQUEST_TIMEOUT,
                    )
            response.close()
            is_request_successful = __is_request_successful(response)
        except RequestsConnectionError:
            __LOGGER.error(logging.CONNECTION_ERROR_MESSAGE)
            sleep(program.REQUEST_CONNECTION_ERROR_WAITING_TIME)
        except (ReadTimeout, KeyError):
            __LOGGER.error(logging.READ_TIMEOUT_ERROR_MESSAGE)
            sleep(program.REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME)
    if response:
        return response
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    raise SystemExit()


def __convert_to_raw_data_responses(
    raw_responses: List[Response], flatten: bool
) -> List[Any]:
    """Creates a list with raw data response objects

    Args:
        raw_responses (List[Response]): List of fetched responses
        flatten (bool): Should a possible list of lists be flattend. This assumes
        some knowledge about the handled data strucutes.

    Returns:
        List[Any]: List of raw data objects from raw response objects
    """
    if flatten:
        return list(
            chain(
                *[
                    raw_response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
                    for raw_response in raw_responses
                ]
            )
        )
    return [
        raw_response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
        for raw_response in raw_responses
    ]


def __get_processed_calldata(
    validator_chunk: List[str], calldata_type: CalldataType
) -> str:
    """Processes calldata in dependence of calldata type

    Args:
        validator_chunk (List[str]): List of validators
        calldata_type (CalldataType): Calldata type

    Returns:
        str: Calldata as specific formatted string
    """
    calldata: str = ""
    match calldata_type:
        case CalldataType.REQUEST_DATA:
            calldata = f"[{','.join(validator_chunk)}]"
        case CalldataType.PARAMETERS:
            calldata = f"{','.join(validator_chunk)}"
        case _:
            calldata = ""
    return calldata


def __is_request_successful(response: Response) -> bool:
    """Helper to check if a request was successful

    Args:
        response (Response): Response object from the api call

    Raises:
        RuntimeError: Raised when reponse is totally empty
        KeyError: Raised if no data field is within the response object

    Returns:
        bool: True if request was successful
    """
    if not response.text:
        __LOGGER.error(response)
        raise RuntimeError(logging.NO_RESPONSE_ERROR_MESSAGE)
    if json.RESPONSE_JSON_DATA_FIELD_NAME in response.json():
        return True
    __LOGGER.error(response.text)
    raise KeyError(logging.NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE)
