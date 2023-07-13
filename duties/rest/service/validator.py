"""Service module for updating validator identifiers
"""

from logging import getLogger
from typing import List

from fetcher.data_types import ValidatorIdentifier
from fetcher.parser.validators import (
    update_validator_identifiers as update_global_validator_identifiers,
)
from fetcher.parser.validators import write_updated_validator_identifiers_to_disk

__LOGGER = getLogger()


async def update_validator_identifiers(
    http_method: str, validator_identifiers: List[str]
) -> List[ValidatorIdentifier]:
    """Updates validator identifiers

    Args:
        http_method (str): Used http method
        validator_identifier (List[str]): Provided validator identifiers
    """
    response = await update_global_validator_identifiers(
        http_method, validator_identifiers
    )
    await write_updated_validator_identifiers_to_disk()
    __LOGGER.info("%s validator identifiers: %s", http_method, validator_identifiers)
    if response:
        return list(response.values())
    return [ValidatorIdentifier()]
