"""Service module for checking whether there are any upcoming duties
"""

from helper.help import fetch_upcoming_validator_duties


async def any_upcoming_duties_in_queue() -> bool:
    """Check whether there are upcoming duties for the provided validators

    Returns:
        bool: Are there any upcoming duties in the queue for the provided validators
    """
    duties = await fetch_upcoming_validator_duties()
    if duties:
        return True
    return False
