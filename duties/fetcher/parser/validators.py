"""Module for parsing provided validator identifier
"""

from logging import getLogger
from typing import Any, Dict, List

from cli.arguments import ARGUMENTS
from constants import endpoints, json, logging, program
from eth_typing import BLSPubkey
from fetcher.data_types import ValidatorData, ValidatorIdentifier
from protocol import ethereum
from protocol.request import send_beacon_api_request

__LOGGER = getLogger(__name__)


def get_active_validator_indices() -> List[str]:
    """Creates a list of active validator indices based on the provided user input

    Returns:
        List[str]: List of active validator indices based on the provided user input
    """
    return list(COMPLETE_ACTIVE_VALIDATOR_IDENTIFIERS.keys())


def __create_active_validator_identifiers(
    validator_identifiers: Dict[str, ValidatorIdentifier]
) -> Dict[str, ValidatorIdentifier]:
    """Checks status from provided validators and filters inactives and duplicates

    Args:
        validator_identifiers (Dict[str, ValidatorIdentifier]):
        Raw validator identifiers which were provided by the user

    Returns:
        Dict[str, ValidatorIdentifier]: Active validator identifiers
    """
    if len(validator_identifiers) > program.THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD:
        __LOGGER.info(
            logging.HIGHER_PROCESSING_TIME_INFO_MESSAGE, len(validator_identifiers)
        )
    provided_validators = [
        __get_validator_index_or_pubkey(None, validator)
        for validator in __RAW_PARSED_VALIDATOR_IDENTIFIERS.values()
    ]
    validator_infos = __fetch_validator_infos_from_beacon_chain(provided_validators)
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


def __fetch_validator_infos_from_beacon_chain(
    provided_validators: List[str],
) -> List[Any]:
    """Temporary function to fetch all validators with it's status
    from the beacon chain. Temporary because chunking will be added
    in general to the request functionality

    Args:
        provided_validators (List[str]): Provided validators by the user

    Returns:
        List[Any]: Fetched validator infos from the beacon chain
    """
    chunked_validators = [
        provided_validators[index : index + 300]
        for index in range(0, len(provided_validators), 300)
    ]
    fetched_validator_infos: List[Any] = []
    for chunk in chunked_validators:
        parameter_value = f"{','.join(chunk)}"
        raw_response = send_beacon_api_request(
            endpoint=endpoints.VALIDATOR_STATUS_ENDPOINT,
            parameters={"id": parameter_value},
        )
        fetched_validator_infos.extend(
            raw_response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
        )
    return fetched_validator_infos


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
            and validator_info["status"] in ethereum.ACTIVE_VALIDATOR_STATUS
        ):
            raw_identifier.index = validator_info["index"]
            raw_identifier.validator.pubkey = validator_info["validator"]["pubkey"]
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
    identifier_index = __RAW_PARSED_VALIDATOR_IDENTIFIERS.get(validator_info["index"])
    identifier_pubkey = __RAW_PARSED_VALIDATOR_IDENTIFIERS.get(
        validator_info["validator"]["pubkey"]
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
        for validator in ARGUMENTS.validator_file
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
    if ";" in validator:
        validator = validator.replace(" ", "")
        alias_split = validator.split(";")
        index_or_pubkey = alias_split[0]
        alias = alias_split[1]
        if index_or_pubkey.startswith("0x"):
            if __is_valid_pubkey(index_or_pubkey[2:]):
                return ValidatorIdentifier("", ValidatorData(index_or_pubkey), alias)
        return ValidatorIdentifier(index_or_pubkey, ValidatorData(""), alias)
    if validator.startswith("0x"):
        if __is_valid_pubkey(validator[2:]):
            return ValidatorIdentifier("", ValidatorData(validator), None)
    return ValidatorIdentifier(validator, ValidatorData(""), None)


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
        ) in COMPLETE_ACTIVE_VALIDATOR_IDENTIFIERS.items()
        if validator_identifier.alias
    }


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
        if len(parsed_pubkey) != 48:
            __LOGGER.error(logging.WRONG_OR_INCOMPLETE_PUBKEY_MESSAGE, pubkey)
            raise SystemExit()
    except ValueError as error:
        __LOGGER.error(logging.PUBKEY_IS_NOT_HEXADECIMAL_MESSAGE, pubkey, error)
        raise SystemExit() from error
    return True


__RAW_PARSED_VALIDATOR_IDENTIFIERS = __create_raw_validator_identifiers()
COMPLETE_ACTIVE_VALIDATOR_IDENTIFIERS = __create_active_validator_identifiers(
    __RAW_PARSED_VALIDATOR_IDENTIFIERS
)
COMPLETE_ACTIVE_VALIDATOR_IDENTIFIERS_WITH_ALIAS = (
    __get_validator_identifiers_with_alias()
)
