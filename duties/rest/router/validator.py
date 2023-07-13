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
    """Adds validator identifier to the running eth-duties instance (only in memory)"""
    return await update_validator_identifiers(request.method, validator_identifiers)


@validator_router.delete("/identifier", status_code=status.HTTP_204_NO_CONTENT)
async def delete_validator_identifier(
    validator_identifier: List[str], request: Request
) -> None:
    """Adds validator identifier to the running eth-duties instance (only in memory)"""
    await update_validator_identifiers(request.method, validator_identifier)
