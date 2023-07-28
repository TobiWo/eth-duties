"""Service module for updating validator identifiers
"""

from logging import getLogger
from typing import Dict, List

from fetcher.data_types import ValidatorIdentifier
from fetcher.identifier import core
from fetcher.identifier.parser import update_shared_active_validator_identifiers
from rest.core.types import HttpMethod

__LOGGER = getLogger()


async def update_validator_identifiers(
    provided_validator_identifiers: List[str], http_method: str
) -> List[ValidatorIdentifier] | None:
    """Update validator identifiers in the running eth-duties instance

    Args:
        provided_validator_identifiers (List[str]): Provides validator identifiers
        http_method (str): Request method

    Returns:
        List[ValidatorIdentifier] | None: Response
    """
    provided_raw_validator_identifiers = __create_raw_validator_identifiers_from_list(
        provided_validator_identifiers
    )
    __LOGGER.info(
        "%s validator identifiers: %s", http_method, provided_validator_identifiers
    )
    await update_shared_active_validator_identifiers(
        provided_raw_validator_identifiers, http_method
    )
    if http_method == HttpMethod.POST.value:
        return list(provided_raw_validator_identifiers.values())
    return None


def __create_raw_validator_identifiers_from_list(
    provided_validator_identifiers: List[str],
) -> Dict[str, ValidatorIdentifier]:
    """Parse validator identifiers provided by the user into a identifier dict

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers as provided by the user
    """
    return {
        core.get_validator_index_or_pubkey(
            None, core.create_raw_validator_identifier(str(validator))
        ): core.create_raw_validator_identifier(str(validator))
        for validator in provided_validator_identifiers
    }
