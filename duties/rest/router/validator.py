"""Router module for updating validator identifiers
"""

from typing import List

from fastapi import APIRouter, Request, Response, status
from fetcher.data_types import ValidatorIdentifier
from rest.core.types import BadValidatorIdentifiers
from rest.service.validator import update_validator_identifiers

validator_router = APIRouter(prefix="/validator", tags=["validator"])


@validator_router.post(
    "/identifier",
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": BadValidatorIdentifiers}},
)
async def add_validator_identifier(
    validator_identifiers: List[str], request: Request, response: Response
) -> List[ValidatorIdentifier] | BadValidatorIdentifiers:
    """Add validator identifiers to the running eth-duties instance (only in memory)

    Args:
        validator_identifiers (List[str]): Provided validator identifiers
        request (Request): Sent request
        response (Response): Sent server response

    Returns:
        List[ValidatorIdentifier] | BadValidatorIdentifiers: Added validator identifiers
    """
    return await update_validator_identifiers(
        validator_identifiers, request.method, response
    )


@validator_router.delete(
    "/identifier",
    status_code=status.HTTP_200_OK,
    responses={400: {"model": BadValidatorIdentifiers}},
)
async def delete_validator_identifier(
    validator_identifiers: List[str], request: Request, response: Response
) -> List[ValidatorIdentifier] | BadValidatorIdentifiers:
    """Delete validator identifiers from the running eth-duties instance (only in memory)

    Args:
        validator_identifiers (List[str]): Provided validator identifiers
        request (Request): Sent request
        response (Response): Sent server response

    Returns:
        List[ValidatorIdentifier] | BadValidatorIdentifiers: Deleted validator identifiers
    """
    return await update_validator_identifiers(
        validator_identifiers, request.method, response
    )
