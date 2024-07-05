"""Module for fetching data from a beacon client
"""

from asyncio import TaskGroup, sleep
from enum import Enum
from itertools import chain
from logging import getLogger
from typing import Any, Dict, List
from urllib.parse import urlencode

from cli.arguments import ARGUMENTS
from cli.types import NodeConnectionProperties, NodeType
from constants import endpoints, json, logging, program
from protocol.connection import BeaconNode
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get, post

__LOGGER = getLogger()
beacon_node = BeaconNode()


class CalldataType(Enum):
    """Defines the type of the calldata for the rest call"""

    NONE = 0
    REQUEST_DATA = 1
    PARAMETERS = 2


async def send_beacon_api_request(
    endpoint: str,
    calldata_type: CalldataType,
    provided_validators: List[str] | None = None,
    flatten: bool = True,
) -> List[Any]:
    """Sends api requests to the beacon client and returns the subsequent data objects
    from the responses

    Args:
        endpoint (str): Endpoint which will be called
        calldata_type (CalldataType): The type of calldata submitted with the request
        provided_validators (List[str]): Validator indices or pubkey to get information for
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
                0,
                len(provided_validators),
                program.NUMBER_OF_VALIDATORS_PER_REST_CALL,
            )
        ]
        async with TaskGroup() as taskgroup:
            tasks = [
                taskgroup.create_task(
                    __handle_api_request(
                        NodeConnectionProperties("", NodeType.BEACON),
                        endpoint,
                        calldata_type,
                        chunk,
                    )
                )
                for chunk in chunked_validators
            ]
        responses = [task.result() for task in tasks]
    else:
        responses.append(
            await __handle_api_request(
                NodeConnectionProperties("", NodeType.BEACON),
                endpoint,
                calldata_type,
                [],
            )
        )
    return __convert_to_raw_data_responses(responses, flatten)


async def send_key_manager_api_keystore_requests() -> List[Any]:
    """Send api request to the keystore endpoints of the key manager api of an validator node

    Returns:
        List[Any]: List with validators managed by the node
        (see https://ethereum.github.io/keymanager-APIs/#/ for reference)
    """
    validator_nodes: List[NodeConnectionProperties] = ARGUMENTS.validator_nodes
    async with TaskGroup() as taskgroup:
        tasks = [
            taskgroup.create_task(
                __handle_api_request(node, endpoint, CalldataType.NONE, [""])
            )
            for node in validator_nodes
            for endpoint in [
                endpoints.LOCAL_KEYSTORES_ENDPOINT,
                endpoints.REMOTE_KEYSTORES_ENDPOINT,
            ]
        ]
    responses = [task.result() for task in tasks]
    return __convert_to_raw_data_responses(responses, True)


async def __handle_api_request(
    node_connection_properties: NodeConnectionProperties,
    endpoint: str,
    calldata_type: CalldataType,
    provided_validators: List[str],
) -> Response:
    """Handle a single api request to a beacon or validator node

    Args:
        node_connection_properties (NodeConnectionProperties): Object
        with respective connection information
        endpoint (str): Endpoint which will be called
        calldata_type (CalldataType): The type of calldata submitted with the request
        provided_validators (List[str]): Validator indices or pubkey to get information for

    Raises:
        SystemExit: Program exit if the response is not present at all
        which will happen if the user interrupts at specific moment during
        execution

    Returns:
        Response: Response object with data provided by the endpoint
    """
    is_request_successful = False
    response = Response()
    calldata = __get_processed_calldata(provided_validators, calldata_type)
    retry_counter = 0
    retry_limit = __get_request_retry_limit(node_connection_properties)
    while not is_request_successful or retry_counter == retry_limit:
        node_connection_properties = __get_correct_node_connection_properties(
            node_connection_properties
        )
        try:
            retry_counter += 1
            response = __send_api_request(
                node_connection_properties, endpoint, calldata, calldata_type
            )
            response.close()
            is_request_successful = __is_request_successful(
                response, node_connection_properties.url
            )
        except RequestsConnectionError:
            __LOGGER.error(
                logging.CONNECTION_ERROR_MESSAGE,
                node_connection_properties.node_type.value,
                node_connection_properties.url,
            )
            await sleep(program.REQUEST_CONNECTION_ERROR_WAITING_TIME)
        except (ReadTimeout, KeyError):
            __LOGGER.error(
                logging.READ_TIMEOUT_ERROR_MESSAGE,
                node_connection_properties.node_type.value,
                node_connection_properties.url,
            )
            await sleep(program.REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME)
        __log_too_many_retries(retry_counter, node_connection_properties)
    return response


def __log_too_many_retries(
    retry_counter: int, node_connection_properties: NodeConnectionProperties
) -> None:
    """Log if too many api request retries are performed

    Args:
        retry_counter (int): Count the number of request retries
        node_url (str): Url to which the request is send
        validator_node (ValidatorNode | None): Validator node object
        with respective connection information
    """
    retry_limit = __get_request_retry_limit(node_connection_properties)
    if retry_counter == retry_limit + 1:
        __LOGGER.error(
            logging.NO_RESPONSE_ERROR_MESSAGE, node_connection_properties.url
        )
        if node_connection_properties.bearer_token:
            __LOGGER.warning(
                logging.NO_FETCHED_VALIDATOR_IDENTIFIERS_MESSAGE,
                node_connection_properties.url,
            )


def __get_correct_node_connection_properties(
    node_connection_properties: NodeConnectionProperties,
) -> NodeConnectionProperties:
    """Get node url in dependence of whether or not to call a validator node

    Args:
        node_connection_properties (NodeConnectionProperties): Object
        with respective connection information

    Returns:
        str: Node url
    """
    if node_connection_properties.bearer_token:
        return node_connection_properties
    return beacon_node.get_healthy_beacon_node(True)


def __get_request_retry_limit(
    node_connection_properties: NodeConnectionProperties,
) -> int:
    """Get request retry limit in dependence of whether or not to call a validator node

    Args:
        node_connection_properties (NodeConnectionProperties): Object
        with respective connection information

    Returns:
        int: Limit for request retries
    """
    if node_connection_properties.bearer_token:
        return 3
    return 1000


def __send_api_request(
    node_connection_properties: NodeConnectionProperties,
    endpoint: str,
    calldata: str,
    calldata_type: CalldataType,
) -> Response:
    """Send consensus layer beacon or validator node api request

    Args:
        node_connection_properties (NodeConnectionProperties): Object
        with respective connection information
        endpoint (str): API endpoint
        calldata (str): Data which is send alongside the request
        calldata_type (CalldataType): Type of calldata

    Returns:
        Response: Request response
    """
    response = Response()
    header = __get_correct_request_header(node_connection_properties)
    match calldata_type:
        case CalldataType.REQUEST_DATA:
            response = post(
                url=f"{node_connection_properties.url}{endpoint}",
                data=calldata,
                timeout=program.REQUEST_TIMEOUT,
                headers=header,
            )
        case CalldataType.PARAMETERS:
            parameters = urlencode({"id": calldata}, safe=",")
            response = get(
                url=f"{node_connection_properties.url}{endpoint}",
                params=parameters,
                timeout=program.REQUEST_TIMEOUT,
                headers=header,
            )
        case _:
            response = get(
                url=f"{node_connection_properties.url}{endpoint}",
                timeout=program.REQUEST_TIMEOUT,
                headers=header,
            )
    response.close()
    return response


def __get_correct_request_header(
    node_connection_properties: NodeConnectionProperties,
) -> Dict[str, str]:
    """Get request header in dependence of whether or not to call a validator node

    Args:
        node_connection_properties (NodeConnectionProperties): Object
        with respective connection information

    Returns:
        Dict[str, str]: Request header
    """
    if node_connection_properties.bearer_token:
        header_with_authentication = program.REQUEST_HEADER
        header_with_authentication.update(
            {"Authorization": f"Bearer {node_connection_properties.bearer_token}"}
        )
        return header_with_authentication
    return program.REQUEST_HEADER


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
            calldata = ",".join(f'"{validator}"' for validator in validator_chunk)
            calldata = f"[{calldata}]"
        case CalldataType.PARAMETERS:
            calldata = f"{','.join(validator_chunk)}"
        case _:
            calldata = ""
    return calldata


def __is_request_successful(response: Response, node_url: str) -> bool:
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
        raise RuntimeError(logging.NO_RESPONSE_ERROR_MESSAGE, node_url)
    if json.RESPONSE_JSON_DATA_FIELD_NAME in response.json():
        return True
    __LOGGER.error(response.text)
    raise KeyError(logging.NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE)
