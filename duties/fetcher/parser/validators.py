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
NOT_ALLOWED_CHARACTERS = [".", ","]


def get_active_validator_indices() -> List[str]:
    """Creates a list of active validator indices based on the provided user input

    Returns:
        List[str]: List of active validator indices based on the provided user input
    """
    validator_identifiers = [
        __get_correct_validator_identifier(None, validator)
        for validator in PARSED_VALIDATORS.values()
    ]
    active_validator_indices = __get_active_validator_indices(validator_identifiers)
    return active_validator_indices


def __get_active_validator_indices(validators: List[str]) -> List[str]:
    """Checks status from provided validators and filters out inactive ones

    Args:
        validators (List[str]): Provided validators by the user

    Returns:
        List[str]: Currently active validator indices
    """
    if len(validators) > program.THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD:
        __LOGGER.info(logging.HIGHER_PROCESSING_TIME_INFO_MESSAGE, len(validators))
    fetched_validators = __fetch_validators_from_beacon_chain(validators)
    active_validators = [
        __get_correct_validator_identifier(
            validators, ValidatorIdentifier.from_dict(validator)
        )
        for validator in fetched_validators
        if validator["status"] in ethereum.ACTIVE_VALIDATOR_STATUS
    ]
    inactive_validators = list(set(validators).difference(set(active_validators)))
    if inactive_validators:
        __LOGGER.warning(logging.INACTIVE_VALIDATORS_MESSAGE, inactive_validators)
    return [
        validator["index"]
        for validator in fetched_validators
        if validator["status"] in ethereum.ACTIVE_VALIDATOR_STATUS
    ]


def __fetch_validators_from_beacon_chain(validators: List[str]) -> List[Any]:
    """Temporary function to fetch all validators with it's status
    from the beacon chain

    Args:
        validators (List[str]): List of validator identifiers

    Returns:
        List[Any]: Fetched validators from the beacon chain
    """
    chunked_validators = [
        validators[index : index + 300] for index in range(0, len(validators), 300)
    ]
    fetched_validators: List[Any] = []
    for chunk in chunked_validators:
        parameter_value = f"{','.join(chunk)}"
        raw_response = send_beacon_api_request(
            endpoint=endpoints.VALIDATOR_STATUS_ENDPOINT,
            parameters={"id": parameter_value},
        )
        fetched_validators.extend(
            raw_response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
        )
    return fetched_validators


def __get_correct_validator_identifier(
    validators: List[str] | None, validator: ValidatorIdentifier
) -> str:
    """Checks which validator identifier is present and returns it accordingly

    Args:
        validators (List[str]): Provided validators by the user
        validator (ValidatorIdentifier): Current checked validator identifier

    Returns:
        str: Specific validator identifier
    """
    if validators:
        if validator.index in validators:
            return validator.index
        return validator.validator.pubkey
    if validator.index:
        return validator.index
    return validator.validator.pubkey


def __get_validator_identifiers() -> Dict[str, ValidatorIdentifier]:
    """Parses the validators provided by the user

    Returns:
        Dict[str, ValidatorIdentifier]: Validator identifiers as provided by the user
    """
    provided_validators: Dict[str, ValidatorIdentifier] = {}
    if ARGUMENTS.validators:
        provided_validators = {
            __get_correct_validator_identifier(
                None, __get_full_validator_identifier(str(validator))
            ): __get_full_validator_identifier(str(validator))
            for validator_list in ARGUMENTS.validators
            for validator in validator_list
        }
    else:
        provided_validators = {
            __get_correct_validator_identifier(
                None,
                __get_full_validator_identifier(
                    str(validator).strip().replace("\n", "").replace("\r\n", "")
                ),
            ): __get_full_validator_identifier(
                str(validator).strip().replace("\n", "").replace("\r\n", "")
            )
            for validator in ARGUMENTS.validator_file
        }
    return provided_validators


def __get_validator_identifiers_with_alias() -> Dict[str, ValidatorIdentifier]:
    """Filters for validator identifiers where the user provided an alias

    Returns:
        Dict[str, ValidatorIdentifier]: Validator identifiers with alias
    """
    return {
        main_identifier: full_identifier
        for (main_identifier, full_identifier) in PARSED_VALIDATORS.items()
        if full_identifier.alias
    }


def __get_full_validator_identifier(validator: str) -> ValidatorIdentifier:
    """Creates validator identifier object

    Args:
        validator (str): Validator provided by the user

    Raises:
        SystemExit: If provided validator contains not allowed characters

    Returns:
        ValidatorIdentifier: Full validator identifier
    """
    if any(character in validator for character in NOT_ALLOWED_CHARACTERS):
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
        if alias_split[0].startswith("0x"):
            if __is_valid_pubkey(index_or_pubkey[2:]):
                return ValidatorIdentifier("", ValidatorData(index_or_pubkey), alias)
        return ValidatorIdentifier(index_or_pubkey, ValidatorData(""), alias)
    if validator.startswith("0x"):
        if __is_valid_pubkey(validator[2:]):
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
        if len(parsed_pubkey) != 48:
            __LOGGER.error(logging.WRONG_OR_INCOMPLETE_PUBKEY_MESSAGE, pubkey)
            raise SystemExit()
    except ValueError as error:
        __LOGGER.error(logging.PUBKEY_IS_NOT_HEXADECIMAL_MESSAGE, pubkey, error)
        raise SystemExit() from error
    return True


PARSED_VALIDATORS = __get_validator_identifiers()
PARSED_VALIDATORS_WITH_ALIAS = __get_validator_identifiers_with_alias()
