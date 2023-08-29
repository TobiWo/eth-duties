"""Module for core functions to parse and create complete validator identifiers
"""

from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from pickle import dumps, loads
from sys import exit as sys_exit
from typing import Any, Dict, List

from constants import endpoints, json, logging, program
from eth_typing import BLSPubkey
from fetcher.data_types import ValidatorData, ValidatorIdentifier
from fetcher.identifier.filter import log_inactive_and_duplicated_validators
from protocol import ethereum
from protocol.request import CalldataType, send_beacon_api_request

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
                "", ValidatorData(provided_validator_identifier), None
            )
    if provided_validator_identifier.isdigit():
        return ValidatorIdentifier(
            provided_validator_identifier, ValidatorData(""), None
        )
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
            return ValidatorIdentifier("", ValidatorData(index_or_pubkey), alias)
    if index_or_pubkey.isdigit():
        return ValidatorIdentifier(index_or_pubkey, ValidatorData(""), alias)
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


async def fetch_active_validator_identifiers(
    provided_raw_validator_identifiers: dict[str, ValidatorIdentifier]
) -> dict[str, ValidatorIdentifier]:
    """Fetch active validators based on on-chain status

    Args:
        provided_raw_validator_identifiers (dict[str, ValidatorIdentifier]): Provided validator
        identifiers by the user
    Returns:
        dict[str, ValidatorIdentifier]: Active validator identifiers
    """
    if (
        len(provided_raw_validator_identifiers)
        > program.THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD
    ):
        __LOGGER.info(
            logging.HIGHER_PROCESSING_TIME_INFO_MESSAGE,
            len(provided_raw_validator_identifiers),
        )
    provided_validators = [
        get_validator_index_or_pubkey(None, validator)
        for validator in provided_raw_validator_identifiers.values()
    ]
    validator_infos = await send_beacon_api_request(
        endpoint=endpoints.VALIDATOR_STATUS_ENDPOINT,
        calldata_type=CalldataType.PARAMETERS,
        provided_validators=provided_validators,
    )
    provided_active_validator_identifiers = (
        __create_complete_active_validator_identifiers(
            validator_infos, provided_validators, provided_raw_validator_identifiers
        )
    )
    return provided_active_validator_identifiers


def __create_complete_active_validator_identifiers(
    fetched_validator_infos: List[Any],
    provided_validators: List[str],
    raw_validator_identifiers: dict[str, ValidatorIdentifier],
) -> Dict[str, ValidatorIdentifier]:
    """Create complete validator identifiers (index, pubkey, alias) and filters
    for inactive ones and duplicates

    Args:
        fetched_validator_infos (List[Any]): Fetched validator infos from the beacon chain
        provided_validators (List[str]): Provided validators by the user

    Returns:
        Dict[str, ValidatorIdentifier]: Complete validator identifiers
        filtered for inactive ones and duplicates
    """
    complete_validator_identifiers: Dict[str, ValidatorIdentifier] = {}
    for validator_info in fetched_validator_infos:
        raw_identifier = __get_raw_validator_identifier(
            validator_info, raw_validator_identifiers
        )
        if (
            raw_identifier
            and validator_info[json.RESPONSE_JSON_STATUS_FIELD_NAME]
            in ethereum.ACTIVE_VALIDATOR_STATUS
        ):
            raw_identifier.index = validator_info[json.RESPONSE_JSON_INDEX_FIELD_NAME]
            raw_identifier.validator.pubkey = validator_info[
                json.RESPONSE_JSON_VALIDATOR_FIELD_NAME
            ][json.RESPONSE_JSON_PUBKEY_FIELD_NAME]
            complete_validator_identifiers[raw_identifier.index] = raw_identifier
    log_inactive_and_duplicated_validators(
        provided_validators, complete_validator_identifiers
    )
    return complete_validator_identifiers


def __get_raw_validator_identifier(
    validator_info: Any,
    raw_validator_identifiers: dict[str, ValidatorIdentifier],
) -> ValidatorIdentifier | None:
    """Get raw validator identifier as provided by the user based on the
    fetched validator infos from the beacon chain

    Args:
        validator_info (Any): Validator infos from the beacon chain

    Returns:
        ValidatorIdentifier | None: Raw validator identifier
    """
    identifier_index = raw_validator_identifiers.get(
        validator_info[json.RESPONSE_JSON_INDEX_FIELD_NAME]
    )
    identifier_pubkey = raw_validator_identifiers.get(
        validator_info[json.RESPONSE_JSON_VALIDATOR_FIELD_NAME][
            json.RESPONSE_JSON_PUBKEY_FIELD_NAME
        ]
    )
    if identifier_index and identifier_pubkey:
        if identifier_index.alias:
            return identifier_index
        return identifier_pubkey
    if identifier_index:
        return identifier_index
    return identifier_pubkey
