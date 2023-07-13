"""Service module for fetching raw validator duties
"""

from typing import List

from fetcher.data_types import ValidatorDuty
from fetcher.fetch import (
    get_next_attestation_duties,
    get_next_proposing_duties,
    get_next_sync_committee_duties,
)


async def fetch_raw_attestation_duties() -> List[ValidatorDuty]:
    """Fetches upcoming attestation duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming attestation duties
    """
    upcoming_attestation_duties = await get_next_attestation_duties()
    return list(upcoming_attestation_duties.values())


async def fetch_raw_sync_committeen_duties() -> List[ValidatorDuty]:
    """Fetches upcoming sync-committee duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming sync-committee duties
    """
    upcoming_sync_committee_duties = await get_next_sync_committee_duties()
    return list(upcoming_sync_committee_duties.values())


async def fetch_raw_proposing_duties() -> List[ValidatorDuty]:
    """Fetches upcoming block proposing duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming block proposing duties
    """
    upcoming_proposing_duties = await get_next_proposing_duties()
    return list(upcoming_proposing_duties.values())
