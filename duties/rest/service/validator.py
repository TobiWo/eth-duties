"""Service module for updating validator identifiers
"""

from logging import getLogger
from typing import Dict, List

from constants import logging
from fastapi import Response, status
from fetcher.data_types import ValidatorIdentifier
from fetcher.identifier import core
from fetcher.identifier.filter import filter_empty_validator_identifier
from fetcher.identifier.parser import (
    update_shared_active_validator_identifiers_from_rest_input,
)
from rest.core.types import BadValidatorIdentifiers

__LOGGER = getLogger()


async def update_validator_identifiers(
    provided_validator_identifiers: List[str], http_method: str, response: Response
) -> List[ValidatorIdentifier] | BadValidatorIdentifiers:
    """Update validator identifiers in the running eth-duties instance

    Args:
        provided_validator_identifiers (List[str]): Provided validator identifiers
        http_method (str): Request method
        response (Response): Sent server response

    Returns:
        List[ValidatorIdentifier] | BadValidatorIdentifiers: Response
    """
    provided_raw_validator_identifiers = __create_raw_validator_identifiers_from_list(
        provided_validator_identifiers
    )
    if len(provided_raw_validator_identifiers) == 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return BadValidatorIdentifiers(identifiers=provided_validator_identifiers)
    await update_shared_active_validator_identifiers_from_rest_input(
        provided_raw_validator_identifiers, http_method
    )
    __LOGGER.info(
        logging.MODIFIED_VALIDATOR_IDENTIFIER_MESSAGE,
        http_method,
        list(provided_raw_validator_identifiers.keys()),
    )
    return list(provided_raw_validator_identifiers.values())


def __create_raw_validator_identifiers_from_list(
    provided_validator_identifiers: List[str],
) -> Dict[str, ValidatorIdentifier]:
    """Parse validator identifiers provided by the user into a identifier dict

    Args:
        provided_validator_identifiers (List[str]): Provided validator identifiers

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers as provided by the user
    """
    return filter_empty_validator_identifier(
        {
            core.get_validator_index_or_pubkey(
                None, core.create_raw_validator_identifier(str(validator), True)
            ): core.create_raw_validator_identifier(str(validator), False)
            for validator in provided_validator_identifiers
        }
    )
