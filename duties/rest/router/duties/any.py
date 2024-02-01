"""Router module whether there are any upcoming duties
"""

from fastapi import APIRouter, Response, status

from duties.rest.core.types import NoBeaconNodeConnection, ValidatorDuties
from duties.rest.service.duties.any import any_upcoming_duties_in_queue

any_duties_router = APIRouter(prefix="/duties/any", tags=["duties"])


@any_duties_router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={503: {"model": NoBeaconNodeConnection}},
)
async def are_upcoming_duties_in_queue(
    response: Response,
) -> ValidatorDuties | NoBeaconNodeConnection:
    """Check whether there are upcoming duties for the provided validators

    Returns:
        bool: Are there any duties in the queue for the provided validators
    """
    return await any_upcoming_duties_in_queue(response)
    return await any_upcoming_duties_in_queue(response)
