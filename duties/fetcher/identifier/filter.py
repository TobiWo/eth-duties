"""Module for main filter function which filters for inactive and duplicate validator identifiers
"""

from logging import getLogger
from typing import Dict, List

from constants import logging
from fetcher.data_types import ValidatorIdentifier
from fetcher.identifier import core

__LOGGER = getLogger()


def filter_empty_validator_identifier(
    validator_identifiers: Dict[str, ValidatorIdentifier]
) -> Dict[str, ValidatorIdentifier]:
    """Filter for empty validator identifiers

    Args:
        validator_identifiers (Dict[str, ValidatorIdentifier]): Raw validator identifiers

    Returns:
        Dict[str, ValidatorIdentifier]: Filtered validator identifiers
    """
    return {
        index_or_pubkey: validator_identifier
        for (index_or_pubkey, validator_identifier) in validator_identifiers.items()
        if index_or_pubkey != ""
    }


def log_inactive_and_duplicated_validators(
    provided_validators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> None:
    """Log inactive and duplicated validators to the console

    Args:
        provided_validators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator identifiers filtered for inactive ones and duplicates # pylint: disable=line-too-long
    """
    active_validators = [
        core.get_validator_index_or_pubkey(provided_validators, identifier)
        for identifier in complete_validator_identifiers.values()
    ]
    potentital_inactive_validators = list(
        set(provided_validators).difference(set(active_validators))
    )
    duplicates = __get_duplicates_with_different_identifiers(
        provided_validators, complete_validator_identifiers
    )
    inactive_validators = [
        validator
        for validator in potentital_inactive_validators
        if validator not in duplicates and validator != ""
    ]
    if inactive_validators:
        __LOGGER.warning(logging.INACTIVE_VALIDATORS_MESSAGE, inactive_validators)


def __get_duplicates_with_different_identifiers(
    provided_valdiators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> List[str]:
    """Filter for duplicated validators which were provided with different identifiers

    Args:
        provided_valdiators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator identifiers filtered for inactive ones and duplicates # pylint: disable=line-too-long

    Returns:
        List[str]: Duplicated validator indices and pubkeys
    """
    duplicates = {
        index: identifier
        for (index, identifier) in complete_validator_identifiers.items()
        if identifier.index in provided_valdiators
        and identifier.validator.pubkey in provided_valdiators
    }
    if duplicates:
        __LOGGER.warning(logging.DUPLICATE_VALIDATORS_MESSAGE, list(duplicates.keys()))
    return list(duplicates.keys()) + [
        duplicate.validator.pubkey for duplicate in duplicates.values()
    ]
