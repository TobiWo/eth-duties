"""Module for parsing provided validator identifiers
"""

from asyncio import run, sleep
from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from sys import exit as sys_exit
from typing import Any, Dict, List

from cli.arguments import ARGUMENTS
from constants import endpoints, json, logging, program
from fetcher.data_types import ValidatorIdentifier
from fetcher.fetch import update_validator_identifier_cache
from fetcher.identifier import core
from fetcher.identifier.filter import (
    filter_empty_validator_identifier,
    log_inactive_and_duplicated_validators,
)
from helper.error import NoDataFromEndpointError
from protocol.ethereum import ACTIVE_VALIDATOR_STATUS
from protocol.request import (
    CalldataType,
    send_beacon_api_request,
    send_key_manager_api_keystore_requests,
)
from rest.core.types import HttpMethod

__LOGGER = getLogger()


async def create_shared_active_validator_identifiers(
    active_validator_identifiers: Dict[str, ValidatorIdentifier] | None = None,
) -> None:
    """Create validator identifiers based on the on-chain status in shared memory

    Args:
        active_validator_identifiers (Dict[str, ValidatorIdentifier] | None, optional): Active validator identifiers stored in shared memory. Defaults to None. # pylint: disable=line-too-long
    """
    shared_active_validator_identifiers = SharedMemory(
        program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME, False
    )
    if not active_validator_identifiers:
        active_validator_identifiers = await __fetch_active_validator_identifiers(
            await __get_raw_validator_identifiers_from_cli()
        )
    core.write_validator_identifiers_to_shared_memory(
        shared_active_validator_identifiers, active_validator_identifiers
    )
    core.create_shared_active_validator_identifiers_with_alias()


async def update_shared_active_validator_identifiers_from_rest_input(
    provided_raw_validator_identifiers: Dict[str, ValidatorIdentifier],
    http_method: str,
) -> None:
    """Update the active validator identifiers in shared memory

    Args:
        provided_raw_validator_identifiers (Dict[str, ValidatorIdentifier]): Provided validator identifiers by the user # pylint: disable=line-too-long
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


async def update_shared_active_validator_identifiers_on_interval() -> None:
    """Update stored validator identifiers on specified interval via keymanager api"""
    while True:
        await sleep(ARGUMENTS.validator_update_interval * 60)
        if ARGUMENTS.validator_nodes:
            __LOGGER.info(logging.UPDATE_VALIDATOR_IDENTIFIER_MESSAGE)
            active_validator_identifiers = await __fetch_active_validator_identifiers(
                await __get_raw_validator_identifiers_from_cli()
            )
            await create_shared_active_validator_identifiers(
                active_validator_identifiers
            )
            __set_update_flag_in_shared_memory()


def __set_update_flag_in_shared_memory() -> None:
    """Create a shared memory instance which is used in other processes to check whether validator
    identifiers got updated
    """
    try:
        SharedMemory(program.UPDATED_SHARED_MEMORY_NAME, True, 1).close()
    except FileExistsError:
        pass


async def __fetch_active_validator_identifiers(
    provided_raw_validator_identifiers: dict[str, ValidatorIdentifier]
) -> dict[str, ValidatorIdentifier]:
    """Fetch active validators based on on-chain status

    Args:
        provided_raw_validator_identifiers (dict[str, ValidatorIdentifier]): Provided validator identifiers by the user # pylint: disable=line-too-long

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
    try:
        validator_infos = await send_beacon_api_request(
            endpoint=endpoints.VALIDATOR_STATUS_ENDPOINT,
            calldata_type=CalldataType.PARAMETERS,
            provided_validators=provided_validators,
        )
    except NoDataFromEndpointError:
        validator_infos = []
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
        raw_validator_identifiers (dict[str, ValidatorIdentifier]): Validator identifiers provided by the user or fetched via keymanager api # pylint: disable=line-too-long

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
        raw_validator_identifiers (dict[str, ValidatorIdentifier]): Validator identifiers provided by the user or fetched via keymanager api # pylint: disable=line-too-long

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


async def __get_raw_validator_identifiers_from_cli() -> Dict[str, ValidatorIdentifier]:
    """Parse the validator identifiers provided by the user or fetched from the provided
    validator nodes

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers
    """
    raw_validator_identifiers: Dict[str, ValidatorIdentifier] = {}
    if ARGUMENTS.validators:
        raw_validator_identifiers.update(
            __get_raw_validator_identifiers_from_validators_argument()
        )
    elif ARGUMENTS.validators_file:
        raw_validator_identifiers.update(
            __get_raw_validator_identifiers_from_validators_file_argument()
        )
    if ARGUMENTS.validator_nodes:
        fetched_keystores = await send_key_manager_api_keystore_requests()
        if fetched_keystores:
            raw_validator_identifiers_from_fetched_keystores = (
                __get_raw_validator_identifiers_from_fetched_keystores(
                    fetched_keystores
                )
            )
            raw_validator_identifiers.update(
                raw_validator_identifiers_from_fetched_keystores
            )
        else:
            raw_validator_identifiers.update({"NONE": ValidatorIdentifier()})
    return filter_empty_validator_identifier(raw_validator_identifiers)


def __get_raw_validator_identifiers_from_validators_argument() -> (
    Dict[str, ValidatorIdentifier]
):
    """Create raw validator identifiers from --validators cli argument

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers
    """
    return {
        core.get_validator_index_or_pubkey(
            None, core.create_raw_validator_identifier(str(validator), True)
        ): core.create_raw_validator_identifier(str(validator), False)
        for validator_list in ARGUMENTS.validators
        for validator in validator_list
    }


def __get_raw_validator_identifiers_from_validators_file_argument() -> (
    Dict[str, ValidatorIdentifier]
):
    """Create raw validator identifiers from --validators-file cli argument

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers
    """
    return {
        core.get_validator_index_or_pubkey(
            None,
            core.create_raw_validator_identifier(
                str(validator).strip().replace("\n", "").replace("\r\n", ""), True
            ),
        ): core.create_raw_validator_identifier(
            str(validator).strip().replace("\n", "").replace("\r\n", ""), False
        )
        for validator in ARGUMENTS.validators_file
    }


def __get_raw_validator_identifiers_from_fetched_keystores(
    fetched_keystores: List[Any],
) -> Dict[str, ValidatorIdentifier]:
    """Create raw validator identifiers from validators managed by the connected validator nodes
    supplied via --validator-nodes cli argument

    Args:
        fetched_keystores (List[Any]): Validators managed by the fetched validator nodes

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers
    """
    validator_identifiers: Dict[str, ValidatorIdentifier] = {}
    for keystore in fetched_keystores:
        validator_identifiers.update(
            __get_raw_validator_identifier_from_keystore(keystore)
        )
    __LOGGER.info(
        logging.LOADED_VALIDATOR_IDENTIFIER_MESSAGE,
        len(validator_identifiers.keys()),
    )
    return validator_identifiers


def __get_raw_validator_identifier_from_keystore(
    keystore: Any,
) -> Dict[str, ValidatorIdentifier]:
    """Get raw validator identifier from validators managed by the connected validator nodes
    which are either managed by the validator client locally or externally by a remote signer

    Args:
        keystore (Any): Validators managed by connected validator nodes

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifier
    """
    if json.RESPONSE_JSON_VALIDATING_PUBKEY_NAME in keystore:
        key = json.RESPONSE_JSON_VALIDATING_PUBKEY_NAME
    else:
        key = json.RESPONSE_JSON_PUBKEY_FIELD_NAME
    return {
        core.get_validator_index_or_pubkey(
            None,
            core.create_raw_validator_identifier(keystore[key], True),
        ): core.create_raw_validator_identifier(keystore[key], False)
    }


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
    run(create_shared_active_validator_identifiers())
    update_validator_identifier_cache()
except KeyboardInterrupt:
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    sys_exit(1)
