"""Service module for fetching raw validator duties
"""

from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import wait_for
from typing import List

from constants import program
from fastapi import Response, status
from fetcher.data_types import ValidatorDuty
from fetcher.fetch import (
    fetch_upcoming_attestation_duties,
    fetch_upcoming_proposing_duties,
    fetch_upcoming_sync_committee_duties,
)
from rest.core.types import NoBeaconNodeConnection


async def fetch_raw_attestation_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Fetch upcoming attestation duties for provided validators

    Args:
        response (Response): Attestation duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming attestation duties
    """
    try:
        upcoming_attestation_duties = await wait_for(
            fetch_upcoming_attestation_duties(),
            program.REST_RAW_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT,
        )
        return list(upcoming_attestation_duties.values())
    except AsyncioTimeoutError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return NoBeaconNodeConnection()


async def fetch_raw_sync_committeen_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Fetch upcoming sync-committee duties for provided validators

    Args:
        response (Response): Sync committee duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming sync-committee duties
    """
    try:
        upcoming_sync_committee_duties = await wait_for(
            fetch_upcoming_sync_committee_duties(),
            program.REST_RAW_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT,
        )
        return list(upcoming_sync_committee_duties.values())
    except AsyncioTimeoutError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return NoBeaconNodeConnection()


async def fetch_raw_proposing_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Fetch upcoming block proposing duties for provided validators

    Args:
        response (Response): Proposing duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming block proposing duties
    """
    try:
        upcoming_proposing_duties = await wait_for(
            fetch_upcoming_proposing_duties(),
            program.REST_RAW_DUTY_NO_BEACON_NODE_CONNECTION_TIMEOUT,
        )
        return list(upcoming_proposing_duties.values())
    except AsyncioTimeoutError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return NoBeaconNodeConnection()
