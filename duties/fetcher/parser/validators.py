"""Module for parsing provided validator identifier
"""

import pickle
from asyncio import run
from logging import getLogger
from shutil import rmtree
from sys import exit as sys_exit
from typing import Any, Callable, Dict, List

from cli.arguments import ARGUMENTS
from constants import endpoints, json, logging, program
from eth_typing import BLSPubkey
from fetcher.data_types import ValidatorData, ValidatorIdentifier
from protocol import ethereum
from protocol.request import CalldataType, send_beacon_api_request
from rest.core.types import HttpMethod

__LOGGER = getLogger()


def get_active_validator_indices() -> List[str]:
    """Creates a list of active validator indices based on the provided user input

    Returns:
        List[str]: List of active validator indices based on the provided user input
    """
    return list(__complete_active_validator_identifiers.keys())


async def update_validator_identifiers(
    http_method: str,
    validator_identifiers: List[str],
) -> Dict[str, ValidatorIdentifier] | None:
    """Adds or deletes validator identifiers from rest call in dependence of the used http method

    Args:
        http_method (str): The used http method
        validator_identifiers (List[str]): Provided validator identifiers
    """
    if http_method == HttpMethod.DELETE.value:
        __delete_validator_identifiers(validator_identifiers)
    elif http_method == HttpMethod.POST.value:
        provided_raw_validator_identifiers = (
            __create_raw_validator_identifiers_from_list(validator_identifiers)
        )
        __raw_parsed_validator_identifiers.update(provided_raw_validator_identifiers)
        return provided_raw_validator_identifiers
    elif http_method != HttpMethod.GET:
        __LOGGER.warning(logging.NOT_SUPPORTED_HTTP_METHOD_MESSAGE, http_method)
    return None


def __delete_validator_identifiers(validator_identifiers: List[str]) -> None:
    """Deletes validator identifiers

    Args:
        validator_identifiers (List[str]): Provided validator identifiers
    """
    for provided_identifier in validator_identifiers:
        is_validator_identifier_present = (
            provided_identifier in __raw_parsed_validator_identifiers.keys()
        )
        if is_validator_identifier_present:
            __raw_parsed_validator_identifiers.pop(provided_identifier, None)
            continue
        for (
            complete_active_validator_identifier
        ) in __complete_active_validator_identifiers.values():
            if provided_identifier in (
                complete_active_validator_identifier.index,
                complete_active_validator_identifier.validator.pubkey,
            ):
                __raw_parsed_validator_identifiers.pop(
                    complete_active_validator_identifier.validator.pubkey, None
                )
                __raw_parsed_validator_identifiers.pop(
                    complete_active_validator_identifier.index, None
                )


def __create_raw_validator_identifiers_from_list(
    validator_list: List[str],
) -> Dict[str, ValidatorIdentifier]:
    """Parses validators provided by the user via rest call.

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers as provided by the user
    """
    return {
        __get_validator_index_or_pubkey(
            None, __create_raw_validator_identifier(str(validator))
        ): __create_raw_validator_identifier(str(validator))
        for validator in validator_list
    }


async def write_updated_validator_identifiers_to_disk() -> None:
    """Writes the updated validator identifiers temporarily to disk. This is used to share
    data between different processes. This will be changed in the future to a more
    enhanced solution.
    """
    program.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(program.VALIDATOR_IDENTIFIER_TEMP_PATH, "wb") as file_path:
        pickle.dump(__raw_parsed_validator_identifiers, file_path)


async def load_updated_validator_identifiers_into_memory(
    update_identifiers_for_fetcher: Callable[[], None]
) -> None:
    """Loads the temporarily saved identifiers from disk (file) into memory

    Args:
        update_identifiers_for_fetcher (Callable[[], None]): Function to update the validator
        identifiers in the fetch module
    """
    # pylint: disable=global-statement, invalid-name
    global __raw_parsed_validator_identifiers
    global __complete_active_validator_identifiers
    global complete_active_validator_identifiers_with_alias
    if program.TEMP_DIR.exists():
        with open(program.VALIDATOR_IDENTIFIER_TEMP_PATH, "rb") as file_path:
            __raw_parsed_validator_identifiers = pickle.load(file_path)
        __complete_active_validator_identifiers = (
            await __create_active_validator_identifiers()
        )
        complete_active_validator_identifiers_with_alias = (
            __get_validator_identifiers_with_alias()
        )
        rmtree(program.TEMP_DIR)
        update_identifiers_for_fetcher()


def __get_validator_identifiers_with_alias() -> Dict[str, ValidatorIdentifier]:
    """Filters for validator identifiers where the user provided an alias

    Returns:
        Dict[str, ValidatorIdentifier]: Validator identifiers with alias
    """
    return {
        index: validator_identifier
        for (
            index,
            validator_identifier,
        ) in __complete_active_validator_identifiers.items()
        if validator_identifier.alias
    }


async def __create_active_validator_identifiers() -> Dict[str, ValidatorIdentifier]:
    """Checks status from provided validators and filters inactives and duplicates

    Args:
        validator_identifiers (Dict[str, ValidatorIdentifier]):
        Raw validator identifiers which were provided by the user

    Returns:
        Dict[str, ValidatorIdentifier]: Active validator identifiers
    """
    if (
        len(__raw_parsed_validator_identifiers)
        > program.THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD
    ):
        __LOGGER.info(
            logging.HIGHER_PROCESSING_TIME_INFO_MESSAGE,
            len(__raw_parsed_validator_identifiers),
        )
    provided_validators = [
        __get_validator_index_or_pubkey(None, validator)
        for validator in __raw_parsed_validator_identifiers.values()
    ]
    validator_infos = await send_beacon_api_request(
        endpoint=endpoints.VALIDATOR_STATUS_ENDPOINT,
        calldata_type=CalldataType.PARAMETERS,
        provided_validators=provided_validators,
    )
    return __create_complete_active_validator_identifiers(
        validator_infos, provided_validators
    )


def __get_validator_index_or_pubkey(
    provided_validators: List[str] | None, raw_validator_identifier: ValidatorIdentifier
) -> str:
    """Checks if index or pubkey is present and returns it accordingly

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


def __create_complete_active_validator_identifiers(
    fetched_validator_infos: List[Any], provided_validators: List[str]
) -> Dict[str, ValidatorIdentifier]:
    """Creates complete validator identifiers (index, pubkey, alias) and filters
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
        raw_identifier = __get_raw_validator_identifier(validator_info)
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
    __log_inactive_and_duplicated_validators(
        provided_validators,
        complete_validator_identifiers,
    )
    return complete_validator_identifiers


def __get_raw_validator_identifier(
    validator_info: Any,
) -> ValidatorIdentifier | None:
    """Gets raw validator identifier as provided by the user based on the
    fetched validator infos from the beacon chain

    Args:
        validator_info (Any): Validator infos from the beacon chain

    Returns:
        ValidatorIdentifier | None: Raw validator identifier
    """
    identifier_index = __raw_parsed_validator_identifiers.get(
        validator_info[json.RESPONSE_JSON_INDEX_FIELD_NAME]
    )
    identifier_pubkey = __raw_parsed_validator_identifiers.get(
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


def __log_inactive_and_duplicated_validators(
    provided_validators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> None:
    """Logs inactive and duplicated validators to the console

    Args:
        provided_validators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator
        identifiers filtered for inactive ones and duplicates
    """
    active_validators = [
        __get_validator_index_or_pubkey(provided_validators, identifier)
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
        if validator not in duplicates
    ]
    if inactive_validators:
        __LOGGER.warning(logging.INACTIVE_VALIDATORS_MESSAGE, inactive_validators)


def __get_duplicates_with_different_identifiers(
    provided_valdiators: List[str],
    complete_validator_identifiers: Dict[str, ValidatorIdentifier],
) -> List[str]:
    """Filters for duplicated validators which were provided with different identifiers

    Args:
        provided_valdiators (List[str]): Provided validators by the user
        complete_validator_identifiers (Dict[str, ValidatorIdentifier]): Complete validator
        identifiers filtered for inactive ones and duplicates

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


def __create_raw_validator_identifiers() -> Dict[str, ValidatorIdentifier]:
    """Parses the validators provided by the user.

    Returns:
        Dict[str, ValidatorIdentifier]: Raw validator identifiers as provided by the user
    """
    if ARGUMENTS.validators:
        return {
            __get_validator_index_or_pubkey(
                None, __create_raw_validator_identifier(str(validator))
            ): __create_raw_validator_identifier(str(validator))
            for validator_list in ARGUMENTS.validators
            for validator in validator_list
        }
    return {
        __get_validator_index_or_pubkey(
            None,
            __create_raw_validator_identifier(
                str(validator).strip().replace("\n", "").replace("\r\n", "")
            ),
        ): __create_raw_validator_identifier(
            str(validator).strip().replace("\n", "").replace("\r\n", "")
        )
        for validator in ARGUMENTS.validators_file
    }


def __create_raw_validator_identifier(validator: str) -> ValidatorIdentifier:
    """Creates raw validator identifier object

    Args:
        validator (str): Validator provided by the user

    Raises:
        SystemExit: If provided validator contains not allowed characters

    Returns:
        ValidatorIdentifier: Raw validator identifier
    """
    if any(
        character in validator
        for character in program.NOT_ALLOWED_CHARACTERS_FOR_VALIDATOR_PARSING
    ):
        __LOGGER.error(
            logging.WRONG_CHARACTER_IN_PROVIDED_VALIDATOR_IDENTIFIER_MESSAGE,
            validator,
        )
        raise SystemExit()
    if program.ALIAS_SEPARATOR in validator:
        validator = validator.replace(" ", "")
        alias_split = validator.split(program.ALIAS_SEPARATOR)
        index_or_pubkey = alias_split[0]
        alias = alias_split[1]
        if index_or_pubkey.startswith(program.PUBKEY_PREFIX):
            if __is_valid_pubkey(index_or_pubkey[len(program.PUBKEY_PREFIX) :]):
                return ValidatorIdentifier("", ValidatorData(index_or_pubkey), alias)
        return ValidatorIdentifier(index_or_pubkey, ValidatorData(""), alias)
    if validator.startswith(program.PUBKEY_PREFIX):
        if __is_valid_pubkey(validator[len(program.PUBKEY_PREFIX) :]):
            return ValidatorIdentifier("", ValidatorData(validator), None)
    return ValidatorIdentifier(validator, ValidatorData(""), None)


def __is_valid_pubkey(pubkey: str) -> bool:
    """Checks whether the provided pubkey is valid

    Args:
        pubkey (str): Provided pubkey by the user

    Raises:
        SystemExit: If provided pubkey has wrong length
        SystemExit: If provided pubkey is not hexadecimal

    Returns:
        bool: True if pubkey is valid
    """
    try:
        parsed_pubkey = BLSPubkey(bytes.fromhex(pubkey))
        if len(parsed_pubkey) != program.PUBKEY_LENGTH:
            __LOGGER.error(logging.WRONG_OR_INCOMPLETE_PUBKEY_MESSAGE, pubkey)
            raise SystemExit()
    except ValueError as error:
        __LOGGER.error(logging.PUBKEY_IS_NOT_HEXADECIMAL_MESSAGE, pubkey, error)
        raise SystemExit() from error
    return True


try:
    __raw_parsed_validator_identifiers = __create_raw_validator_identifiers()
    __complete_active_validator_identifiers = run(
        __create_active_validator_identifiers()
    )
    complete_active_validator_identifiers_with_alias = (
        __get_validator_identifiers_with_alias()
    )
except KeyboardInterrupt:
    __LOGGER.error(logging.SYSTEM_EXIT_MESSAGE)
    sys_exit(1)
