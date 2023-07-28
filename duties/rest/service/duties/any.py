"""Service module for checking whether there are any upcoming duties
"""

from fetcher.fetch import (
    get_next_attestation_duties,
    get_next_proposing_duties,
    get_next_sync_committee_duties,
)
from helper.help import sort_duties


async def any_upcoming_duties_in_queue() -> bool:
    """Check whether there are upcoming duties for the provided validators

    Returns:
        bool: Are there any upcoming duties in the queue for the provided validators
    """
    upcoming_attestation_duties = await get_next_attestation_duties()
    upcoming_sync_committee_duties = await get_next_sync_committee_duties()
    upcoming_proposing_duties = await get_next_proposing_duties()
    duties = [
        duty
        for duties in [
            upcoming_attestation_duties,
            upcoming_proposing_duties,
            upcoming_sync_committee_duties,
        ]
        for duty in duties.values()
    ]
    duties.sort(key=sort_duties)
    if duties:
        return True
    return False
