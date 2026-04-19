"""Router module for updating validator identifiers
"""

from typing import List

from fastapi import APIRouter, Body, Request, Response, status
from fetcher.data_types import ValidatorIdentifier
from rest.core.types import BadValidatorIdentifiers
from rest.service.validator import update_validator_identifiers

validator_router = APIRouter(prefix="/validator", tags=["validator"])

__VALIDATOR_IDENTIFIERS_BODY_EXAMPLE = [
    "123456",
    "0x93247f2209abcacf57b75a51dafae777f9dd38bc7053d1af526f220a7489a6d3a2753e5f3e8b1cfe39b56f43611df74a;validator-alias",  # pylint: disable=line-too-long
    "234567;proposer-one",
]


@validator_router.post(
    "/identifier",
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": BadValidatorIdentifiers}},
)
async def add_validator_identifier(
    request: Request,
    response: Response,
    validator_identifiers: List[str] = Body(
        ..., examples=[__VALIDATOR_IDENTIFIERS_BODY_EXAMPLE]
    ),
) -> List[ValidatorIdentifier] | BadValidatorIdentifiers:
    """Add validator identifiers to the running eth-duties instance (only in memory)

    Args:
        request (Request): Sent request
        response (Response): Sent server response
        validator_identifiers (List[str]): Provided validator identifiers. Each entry may
            be a validator index, a pubkey, or either with a `;alias` suffix.

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
    request: Request,
    response: Response,
    validator_identifiers: List[str] = Body(
        ..., examples=[__VALIDATOR_IDENTIFIERS_BODY_EXAMPLE]
    ),
) -> List[ValidatorIdentifier] | BadValidatorIdentifiers:
    """Delete validator identifiers from the running eth-duties instance (only in memory)

    Args:
        request (Request): Sent request
        response (Response): Sent server response
        validator_identifiers (List[str]): Provided validator identifiers. Each entry may
            be a validator index, a pubkey, or either with a `;alias` suffix.

    Returns:
        List[ValidatorIdentifier] | BadValidatorIdentifiers: Deleted validator identifiers
    """
    return await update_validator_identifiers(
        validator_identifiers, request.method, response
    )
