"""Router module for updating validator identifiers
"""

from typing import List

from fastapi import APIRouter, Request, status
from fetcher.data_types import ValidatorIdentifier
from rest.service.validator import update_validator_identifiers

validator_router = APIRouter(prefix="/validator", tags=["validator"])


@validator_router.post("/identifier", status_code=status.HTTP_201_CREATED)
async def add_validator_identifier(
    validator_identifiers: List[str], request: Request
) -> List[ValidatorIdentifier]:
    """Add validator identifiers to the running eth-duties instance (only in memory)_summary_

    Args:
        validator_identifiers (List[str]): Provided validator identifiers
        request (Request): Sent request

    Returns:
        List[ValidatorIdentifier]: Provided validator identifiers
    """
    response = await update_validator_identifiers(validator_identifiers, request.method)
    if response:
        return response
    return []


@validator_router.delete("/identifier", status_code=status.HTTP_204_NO_CONTENT)
async def delete_validator_identifier(
    validator_identifier: List[str], request: Request
) -> None:
    """Delete validator identifiers from the running eth-duties instance (only in memory)

    Args:
        validator_identifier (List[str]): Provided validator identifiers
        request (Request): Sent request
    """
    await update_validator_identifiers(validator_identifier, request.method)
