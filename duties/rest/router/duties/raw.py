"""Router module for raw upcoming duties
"""

from typing import List

from fastapi import APIRouter, status
from fetcher.data_types import ValidatorDuty
from rest.service.duties.raw import (
    fetch_raw_attestation_duties,
    fetch_raw_proposing_duties,
    fetch_raw_sync_committeen_duties,
)

raw_duties_router = APIRouter(prefix="/duties/raw", tags=["duties"])


@raw_duties_router.get("/attestation", status_code=status.HTTP_200_OK)
async def get_attestation_duties() -> List[ValidatorDuty]:
    """Get upcoming attestation duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming attestation duties
    """
    return await fetch_raw_attestation_duties()


@raw_duties_router.get("/sync-committee", status_code=status.HTTP_200_OK)
async def get_sync_committee_duties() -> List[ValidatorDuty]:
    """Get upcoming sync committee duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming sync committee duties
    """
    return await fetch_raw_sync_committeen_duties()


@raw_duties_router.get("/proposing", status_code=status.HTTP_200_OK)
async def get_proposing_duties() -> List[ValidatorDuty]:
    """Get upcoming block proposing duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming block proposing duties
    """
    return await fetch_raw_proposing_duties()
