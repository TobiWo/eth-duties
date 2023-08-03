"""Service module for fetching raw validator duties
"""

from typing import List

from fetcher.data_types import ValidatorDuty
from fetcher.fetch import (
    fetch_upcoming_attestation_duties,
    fetch_upcoming_proposing_duties,
    fetch_upcoming_sync_committee_duties,
)


async def fetch_raw_attestation_duties() -> List[ValidatorDuty]:
    """Fetch upcoming attestation duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming attestation duties
    """
    upcoming_attestation_duties = await fetch_upcoming_attestation_duties()
    return list(upcoming_attestation_duties.values())


async def fetch_raw_sync_committeen_duties() -> List[ValidatorDuty]:
    """Fetch upcoming sync-committee duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming sync-committee duties
    """
    upcoming_sync_committee_duties = await fetch_upcoming_sync_committee_duties()
    return list(upcoming_sync_committee_duties.values())


async def fetch_raw_proposing_duties() -> List[ValidatorDuty]:
    """Fetch upcoming block proposing duties for provided validators

    Returns:
        List[ValidatorDuty]: The upcoming block proposing duties
    """
    upcoming_proposing_duties = await fetch_upcoming_proposing_duties()
    return list(upcoming_proposing_duties.values())
