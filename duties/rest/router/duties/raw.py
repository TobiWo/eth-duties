"""Router module for raw upcoming duties
"""

from typing import List

from fastapi import APIRouter, Response, status
from fetcher.data_types import ValidatorDuty
from rest.core.types import NoBeaconNodeConnection
from rest.service.duties.raw import (
    fetch_raw_attestation_duties,
    fetch_raw_proposing_duties,
    fetch_raw_sync_committeen_duties,
)

raw_duties_router = APIRouter(prefix="/duties/raw", tags=["duties"])


@raw_duties_router.get(
    "/attestation",
    status_code=status.HTTP_200_OK,
    responses={503: {"model": NoBeaconNodeConnection}},
)
async def get_attestation_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Get upcoming attestation duties for provided validators

    Args:
        response (Response): Attestation duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming attestation duties
    """
    return await fetch_raw_attestation_duties(response)


@raw_duties_router.get(
    "/sync-committee",
    status_code=status.HTTP_200_OK,
    responses={503: {"model": NoBeaconNodeConnection}},
)
async def get_sync_committee_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Get upcoming sync committee duties for provided validators

    Args:
        response (Response): Sync committee duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming sync committee duties
    """
    return await fetch_raw_sync_committeen_duties(response)


@raw_duties_router.get(
    "/proposing",
    status_code=status.HTTP_200_OK,
    responses={503: {"model": NoBeaconNodeConnection}},
)
async def get_proposing_duties(
    response: Response,
) -> List[ValidatorDuty] | NoBeaconNodeConnection:
    """Get upcoming block proposing duties for provided validators

    Args:
        response (Response): Proposing duty response

    Returns:
        List[ValidatorDuty] | NoBeaconNodeConnection: The upcoming block proposing duties
    """
    return await fetch_raw_proposing_duties(response)
