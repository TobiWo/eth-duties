"""Module which holds all logic for fetching validator duties
"""

from math import ceil
from typing import List
from requests import Response
from fetcher.data_types import ValidatorDuty, DutyType
from constants import endpoints, json
from protocol import protocol
from protocol.request import send_beacon_api_request
from cli.cli import get_arguments


def __get_validator_list() -> List[str]:
    """Creates a list of validators based on the provided user input

    Returns:
        List[str]: List of validators based on the provided user input
    """
    if __ARGUMENTS.validators:
        return __ARGUMENTS.validators
    return [validator.strip() for validator in __ARGUMENTS.validator_file]


__ARGUMENTS = get_arguments()
__VALIDATORS = __get_validator_list()


def get_next_attestation_duties() -> dict[int, ValidatorDuty]:
    """Fetches upcoming attestations (for current and upcoming epoch)
    for all validators which were provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming attestation duties
        for all provided validators
    """
    current_epoch = protocol.get_current_epoch()
    request_data = f"[{','.join(__VALIDATORS)}]"
    is_any_duty_outdated: List[bool] = [True]
    validator_duties: dict[int, ValidatorDuty] = {}
    if __ARGUMENTS.omit_attestation_duties:
        return validator_duties
    while is_any_duty_outdated:
        response_data = __get_raw_response_data(
            current_epoch, DutyType.ATTESTATION, request_data
        )
        validator_duties = {
            data.validator_index: __get_next_attestation_duty(data, validator_duties)
            for data in response_data
        }
        is_any_duty_outdated = [
            True for duty in validator_duties.values() if duty.slot == 0
        ]
        current_epoch += 1
    return validator_duties


def get_next_sync_committee_duties() -> dict[int, ValidatorDuty]:
    """Fetches current and upcoming sync committee duties for all validators
    provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming sync committee duties
        for all provided validators
    """
    current_epoch = protocol.get_current_epoch()
    next_sync_committee_starting_epoch = (
        ceil(current_epoch / protocol.EPOCHS_PER_SYNC_COMMITTEE)
        * protocol.EPOCHS_PER_SYNC_COMMITTEE
    )
    request_data = f"[{','.join(__VALIDATORS)}]"
    validator_duties: dict[int, ValidatorDuty] = {}
    for epoch in [current_epoch, next_sync_committee_starting_epoch]:
        response_data = __get_raw_response_data(
            epoch, DutyType.SYNC_COMMITTEE, request_data
        )
        for data in response_data:
            if data.validator_index not in validator_duties:
                validator_duties[data.validator_index] = ValidatorDuty(
                    data.pubkey,
                    data.validator_index,
                    epoch,
                    0,
                    data.validator_sync_committee_indices,
                    DutyType.SYNC_COMMITTEE,
                )
    return validator_duties


def get_next_proposing_duties() -> dict[int, ValidatorDuty]:
    """Fetches upcoming block proposals for all validators which were
    provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming block proposing duties
        for all provided validators
    """
    current_epoch = protocol.get_current_epoch()
    validator_duties: dict[int, ValidatorDuty] = {}
    for index in [1, 1]:
        response_data = __get_raw_response_data(current_epoch, DutyType.PROPOSING)
        for data in response_data:
            if (
                str(data.validator_index) in __VALIDATORS
                and data.validator_index not in validator_duties
            ):
                validator_duties[data.validator_index] = ValidatorDuty(
                    data.pubkey,
                    data.validator_index,
                    0,
                    data.slot,
                    [],
                    DutyType.PROPOSING,
                )
        current_epoch += index
    return __filter_proposing_duties(validator_duties)


def __get_raw_response_data(
    target_epoch: int, duty_type: DutyType, request_data: str = ""
) -> List[ValidatorDuty]:
    """Fetches raw responses for provided duties

    Args:
        target_epoch (int): Epoch to check for duties
        duty_type (DutyType): Type of the duty
        request_data (str, optional): Request data if any. Defaults to "".

    Returns:
        List[ValidatorDuty]: List of all fetched validator duties for a specific epoch
    """
    response = __fetch_duty_response(target_epoch, duty_type, request_data)
    response_data = response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
    return [ValidatorDuty.from_dict(data) for data in response_data]


def __get_next_attestation_duty(
    data: ValidatorDuty, present_duties: dict[int, ValidatorDuty]
) -> ValidatorDuty:
    """Checks supplied response data for upcoming attestation duty and returns it

    Args:
        data (ValidatorDuty): Response data from rest api call
        present_duties (dict[int, ValidatorDuty]): The already fetched and processed duties

    Returns:
        ValidatorDuty: Validator duty object for the next attestation duty
    """
    current_slot = protocol.get_current_slot()
    if data.validator_index in present_duties:
        present_validator_duty = present_duties[data.validator_index]
        if present_validator_duty.slot != 0:
            return present_validator_duty
    attestation_duty = ValidatorDuty(
        data.pubkey, data.validator_index, 0, 0, [], DutyType.ATTESTATION
    )
    if current_slot >= data.slot:
        return attestation_duty
    attestation_duty.slot = data.slot
    return attestation_duty


def __filter_proposing_duties(
    raw_proposing_duties: dict[int, ValidatorDuty]
) -> dict[int, ValidatorDuty]:
    """Filters supplied proposing duties dict for already outdated duties

    Args:
        raw_proposing_duties (dict[int, ValidatorDuty]): All fetched proposing duties
        for the current and upcoming epoch

    Returns:
        dict[int, ValidatorDuty]: Filtered proposing duties
    """
    current_slot = protocol.get_current_slot()
    filtered_proposing_duties = {
        validator_index: proposing_duty
        for (validator_index, proposing_duty) in raw_proposing_duties.items()
        if proposing_duty.slot > current_slot
    }
    return filtered_proposing_duties


def __fetch_duty_response(
    target_epoch: int, duty_type: DutyType, request_data: str = ""
) -> Response:
    """Fetches validator duties in dependence of the duty type from the beacon client

    Args:
        target_epoch (int): Epoch to fetch duties for
        duty_type (DutyType): Type of the duty
        request_data (str, optional): Request data if any. Defaults to "".

    Returns:
        Response: Raw response from the sent api request
    """
    match duty_type:
        case DutyType.ATTESTATION:
            response = send_beacon_api_request(
                f"{endpoints.ATTESTATION_DUTY_ENDPOINT}{target_epoch}", request_data
            )
        case DutyType.SYNC_COMMITTEE:
            response = send_beacon_api_request(
                f"{endpoints.SYNC_COMMITTEE_DUTY_ENDPOINT}{target_epoch}",
                request_data,
            )
        case DutyType.PROPOSING:
            response = send_beacon_api_request(
                f"{endpoints.BLOCK_PROPOSING_DUTY_ENDPOINT}{target_epoch}"
            )
        case _:
            response = Response()
    return response
