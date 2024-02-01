"""Module for core functions to parse and create complete validator identifiers
"""

from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from pickle import dumps, loads
from sys import exit as sys_exit
from typing import List

from eth_typing import BLSPubkey

from duties.constants import logging, program
from duties.fetcher.data_types import ValidatorData, ValidatorIdentifier

__LOGGER = getLogger()


def read_validator_identifiers_from_shared_memory(
    shared_memory_name: str,
) -> dict[str, ValidatorIdentifier]:
    """Read from shared memory and returns the stored object

    Args:
        shared_memory_name (str): Name of the shared memory instance

    Returns:
        dict[str, ValidatorIdentifier]: Validator identifier dict
    """
    shared_validator_identifiers = SharedMemory(shared_memory_name, False)
    read_bytes = bytes()
    try:
        read_bytes = bytes(shared_validator_identifiers.buf[:10000000])
        shared_validator_identifiers.close()
    except (IndexError, ValueError):
        __LOGGER.error(logging.CANNOT_READ_SHARED_MEMORY_MESSAGE)
        shared_validator_identifiers.close()
        shared_validator_identifiers.unlink()
        sys_exit(1)
    validator_identifiers: dict[str, ValidatorIdentifier] = loads(read_bytes)
    return validator_identifiers


def write_validator_identifiers_to_shared_memory(
    shared_validator_identifiers: SharedMemory,
    validator_identifiers: dict[str, ValidatorIdentifier],
) -> None:
    """Write provided validator identifier dict to shared memory

    Args:
        shared_validator_identifiers (SharedMemory): Shared memory instance where provided dict
        should be stored
        validator_identifiers (dict[str, ValidatorIdentifier]): Validator identifier dict which
        will be stored in shared memory
    """
    try:
        validator_identifiers_bytes = dumps(validator_identifiers)
        shared_validator_identifiers.buf[
            : memoryview(validator_identifiers_bytes).nbytes
        ] = validator_identifiers_bytes
        shared_validator_identifiers.close()
    except (IndexError, ValueError):
        __LOGGER.error(logging.CANNOT_WRITE_SHARED_MEMORY_MESSAGE)
        shared_validator_identifiers.close()
        shared_validator_identifiers.unlink()
        sys_exit(1)


def create_shared_active_validator_identifiers_with_alias() -> None:
    """Filter for validator identifiers where the user provided an alias and stores them
    in shared memory
    """
    active_validator_identifiers = read_validator_identifiers_from_shared_memory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
    )
    shared_active_validator_identifiers_with_alias = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME, False
    )
    identifiers_with_alias = {
        index: validator_identifier
        for (
            index,
            validator_identifier,
        ) in active_validator_identifiers.items()
        if validator_identifier.alias
    }
    write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers_with_alias, identifiers_with_alias
    )


def get_validator_index_or_pubkey(
    provided_validators: List[str] | None, raw_validator_identifier: ValidatorIdentifier
) -> str:
    """Check if index or pubkey is present and returns it accordingly

    Args:
        provided_validators (List[str]): Provided validators by the user
        raw_validator_identifier (ValidatorIdentifier): Validator identifiers

    Returns:
        str: Validator index or pubkey
    """
    if provided_validators:
        if raw_validator_identifier.index in provided_validators:
            return raw_validator_identifier.index
        return raw_validator_identifier.validator.pubkey
    if raw_validator_identifier.index:
        return raw_validator_identifier.index
    return raw_validator_identifier.validator.pubkey


def create_raw_validator_identifier(
    provided_validator_identifier: str, is_logged: bool
) -> ValidatorIdentifier:
    """Create raw validator identifier object

    Args:
        provided_validator_identifier (str): Validator identifier provided by the user
        is_logged (bool): Will log warnings about the provided identifier

    Returns:
        ValidatorIdentifier: Raw validator identifier
    """
    if program.ALIAS_SEPARATOR in provided_validator_identifier:
        full_validator_identifier = __parse_validator_identifier_with_alias(
            provided_validator_identifier, is_logged
        )
        if full_validator_identifier:
            return full_validator_identifier
    if provided_validator_identifier.startswith(program.PUBKEY_PREFIX):
        if __is_valid_pubkey(
            provided_validator_identifier[len(program.PUBKEY_PREFIX) :], is_logged
        ):
            return ValidatorIdentifier(
                validator=ValidatorData(provided_validator_identifier)
            )
    if provided_validator_identifier.isdigit():
        return ValidatorIdentifier(index=provided_validator_identifier)
    if is_logged:
        __LOGGER.warning(
            logging.SKIPPING_PROVIDED_IDENTIFIER_MESSAGE,
            provided_validator_identifier,
        )
    return ValidatorIdentifier()


def __parse_validator_identifier_with_alias(
    provided_validator_identifier_with_alias: str, is_logged: bool
) -> ValidatorIdentifier | None:
    """Parse the provided identifier and alias

    Args:
        provided_validator_identifier (str): Validator identifier provided by the user
        is_logged (bool): Will log errors about the provided pubkey

    Returns:
        ValidatorIdentifier | None: Raw validator identifier with alias
    """
    provided_validator_identifier_with_alias = (
        provided_validator_identifier_with_alias.replace(" ", "")
    )
    alias_split = provided_validator_identifier_with_alias.split(
        program.ALIAS_SEPARATOR
    )
    index_or_pubkey = alias_split[0]
    alias = alias_split[1]
    if index_or_pubkey.startswith(program.PUBKEY_PREFIX):
        if __is_valid_pubkey(index_or_pubkey[len(program.PUBKEY_PREFIX) :], is_logged):
            return ValidatorIdentifier(
                validator=ValidatorData(index_or_pubkey), alias=alias
            )
    if index_or_pubkey.isdigit():
        return ValidatorIdentifier(index=index_or_pubkey, alias=alias)
    return None


def __is_valid_pubkey(pubkey: str, is_logged: bool) -> bool:
    """Check whether the provided pubkey is valid

    Args:
        pubkey (str): Provided pubkey by the user
        is_logged (bool): Will log errors about the provided pubkey

    Returns:
        bool: True if pubkey is valid
    """
    try:
        parsed_pubkey = BLSPubkey(bytes.fromhex(pubkey))
        if len(parsed_pubkey) != program.PUBKEY_LENGTH:
            if is_logged:
                __LOGGER.error(logging.WRONG_OR_INCOMPLETE_PUBKEY_MESSAGE, pubkey)
            return False
    except ValueError as error:
        if is_logged:
            __LOGGER.error(logging.PUBKEY_IS_NOT_HEXADECIMAL_MESSAGE, pubkey, error)
        return False
    return True
    return True
