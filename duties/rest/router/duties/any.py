"""Router module whether there are any upcoming duties
"""

from fastapi import APIRouter, status
from rest.service.duties.any import any_upcoming_duties_in_queue

any_duties_router = APIRouter(prefix="/duties/any", tags=["duties"])


@any_duties_router.get("", status_code=status.HTTP_200_OK)
async def are_upcoming_duties_in_queue() -> bool:
    """Check whether there are upcoming duties for the provided validators

    Returns:
        bool: Are there any duties in the queue for the provided validators
    """
    return await any_upcoming_duties_in_queue()
