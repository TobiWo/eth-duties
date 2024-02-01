"""Module for parsing provided validator identifiers
"""

from asyncio import run
from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from sys import exit as sys_exit
from typing import Any, Dict, List

from duties.cli.arguments import get_arguments
from duties.constants import endpoints, json, logging, program
from duties.fetcher.data_types import ValidatorIdentifier
from duties.fetcher.identifier import core
from duties.fetcher.identifier.filter import (
    filter_empty_validator_identifier,
    log_inactive_and_duplicated_validators,
)
from duties.protocol.ethereum import ACTIVE_VALIDATOR_STATUS
from duties.protocol.request import CalldataType, send_beacon_api_request
from duties.rest.core.types import HttpMethod

__LOGGER = getLogger()
__ARGUMENTS = get_arguments()


def get_active_validator_indices() -> List[str]:
    """Create a list of active validator indices based on the provided user input

    Returns:
        List[str]: List of active validator indices based on the provided user input
    """
    complete_active_validator_identifiers = (
        core.read_validator_identifiers_from_shared_memory(
            program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
        )
    )
    return list(complete_active_validator_identifiers.keys())


async def create_shared_active_validator_identifiers_at_startup() -> None:
    """Create validator identifiers based on the on-chain status in shared memory"""
    shared_active_validator_identifiers = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME, False
    )
    active_validator_identifiers = await __fetch_active_validator_identifiers(
        __get_raw_validator_identifiers_from_cli()
    )
    core.write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers, active_validator_identifiers
    )
    core.create_shared_active_validator_identifiers_with_alias()


async def __fetch_active_validator_identifiers(
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
        core.get_validator_index_or_pubkey(None, validator)
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
            in ACTIVE_VALIDATOR_STATUS
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


def __get_raw_validator_identifiers_from_cli() -> Dict[str, ValidatorIdentifier]:
    """Parse the validator identifiers provided by the user

    Returns:
        Dict[str, ValidatorIdentifier]: Validator identifiers
    """
    raw_validator_identifiers = {}
    if __ARGUMENTS.validators:
        raw_validator_identifiers = {
            core.get_validator_index_or_pubkey(
                None, core.create_raw_validator_identifier(str(validator), True)
            ): core.create_raw_validator_identifier(str(validator), False)
            for validator_list in __ARGUMENTS.validators
            for validator in validator_list
        }
    elif __ARGUMENTS.validators_file:
        raw_validator_identifiers = {
            core.get_validator_index_or_pubkey(
                None,
                core.create_raw_validator_identifier(
                    str(validator).strip().replace("\n", "").replace("\r\n", ""), True
                ),
            ): core.create_raw_validator_identifier(
                str(validator).strip().replace("\n", "").replace("\r\n", ""), False
            )
            for validator in __ARGUMENTS.validators_file
        }
    return filter_empty_validator_identifier(raw_validator_identifiers)


async def update_shared_active_validator_identifiers(
    provided_raw_validator_identifiers: Dict[str, ValidatorIdentifier],
    http_method: str,
) -> None:
    """Update the active validator identifiers in shared memory

    Args:
        provided_raw_validator_identifiers (Dict[str, ValidatorIdentifier]): Provided validator
        identifiers by the user
        http_method (str): REST method
    """
    provided_active_validator_identifiers = await __fetch_active_validator_identifiers(
        provided_raw_validator_identifiers
    )
    current_active_validator_identifiers = (
        core.read_validator_identifiers_from_shared_memory(
            program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
        )
    )
    if http_method == HttpMethod.POST.value:
        current_active_validator_identifiers.update(
            provided_active_validator_identifiers
        )
    else:
        for identifier in provided_active_validator_identifiers.keys():
            current_identifier = current_active_validator_identifiers.get(identifier)
            if current_identifier:
                current_active_validator_identifiers.pop(identifier)
    shared_active_validator_identifiers = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME, False
    )
    core.write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers, current_active_validator_identifiers
    )
    core.create_shared_active_validator_identifiers_with_alias()
    __set_update_flag_in_shared_memory()


def __set_update_flag_in_shared_memory() -> None:
    """Create a shared memory instance which is used in other processes to check whether validator
    identifiers got updated
    """
    try:
        SharedMemory(program.UPDATED_SHARED_MEMORY_NAME, True, 1).close()
    except FileExistsError:
        pass


try:
    SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME,
        True,
        program.SIZE_OF_SHARED_MEMORY,
    )
    SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS_SHARED_MEMORY_NAME,
        True,
        program.SIZE_OF_SHARED_MEMORY,
    )
    run(create_shared_active_validator_identifiers_at_startup())
except KeyboardInterrupt:
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    sys_exit(1)
