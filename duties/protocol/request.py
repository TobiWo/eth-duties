"""Module for fetching data from a beacon client
"""

from logging import getLogger
from time import sleep
from typing import Dict

from cli.arguments import ARGUMENTS
from constants import json, logging, program
from requests import ConnectionError as RequestsConnectionError
from requests import ReadTimeout, Response, get, post

__LOGGER = getLogger(__name__)


def send_beacon_api_request(
    endpoint: str,
    request_data: str | None = None,
    parameters: Dict[str, str] | None = None,
) -> Response:
    """Sends an api request to the beacon client

    Args:
        endpoint (str): The endpoint which will be called
        request_data (str, optional): Request data if any. Defaults to "".

    Raises:
        SystemExit: Program exit if the response is not present at all
        which will happen if the user interrupts at specific moment during
        execution

    Returns:
        Response: Response object with data provided by the endpoint
    """
    is_request_successful = False
    response = None
    while not is_request_successful and not program.GRACEFUL_KILLER.kill_now:
        try:
            if not request_data and not parameters:
                response = get(
                    url=f"{ARGUMENTS.beacon_node}{endpoint}",
                    timeout=program.REQUEST_TIMEOUT,
                )
            elif request_data and not parameters:
                response = post(
                    url=f"{ARGUMENTS.beacon_node}{endpoint}",
                    data=request_data,
                    timeout=program.REQUEST_TIMEOUT,
                )
            else:
                response = get(
                    url=f"{ARGUMENTS.beacon_node}{endpoint}",
                    params=parameters,
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
