"""Service module for checking whether there are any upcoming duties
"""

from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import wait_for

from constants.program import REST_ANY_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT
from fastapi import Response, status
from helper.duty import fetch_upcoming_validator_duties
from rest.core.types import NoBeaconNodeConnection, ValidatorDuties


async def any_upcoming_duties_in_queue(
    response: Response,
) -> ValidatorDuties | NoBeaconNodeConnection:
    """Check whether there are upcoming duties for the provided validators

    Args:
        response (Response): Response object whether any duties are in the queue

    Returns:
        ValidatorDuties | NoBeaconNodeConnection: Are there any upcoming duties in the queue for the provided validators # pylint: disable=line-too-long
    """
    try:
        duties = await wait_for(
            fetch_upcoming_validator_duties(),
            REST_ANY_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT,
        )
        if duties:
            return ValidatorDuties(any=True)
        return ValidatorDuties(any=False)
    except AsyncioTimeoutError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return NoBeaconNodeConnection()
