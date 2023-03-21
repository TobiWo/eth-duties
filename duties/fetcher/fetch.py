"""Module which holds all logic for fetching validator duties
"""

from logging import getLogger
from math import ceil
from typing import List

from cli.arguments import ARGUMENTS
from constants import endpoints, logging
from fetcher.data_types import DutyType, ValidatorDuty
from fetcher.parser.validators import get_active_validator_indices
from protocol import ethereum
from protocol.request import CalldataType, send_beacon_api_request

__VALIDATORS = get_active_validator_indices()
__LOGGER = getLogger(__name__)


def get_next_attestation_duties() -> dict[str, ValidatorDuty]:
    """Fetches upcoming attestations (for current and upcoming epoch)
    for all validators which were provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming attestation duties
        for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    is_any_duty_outdated: List[bool] = [True]
    validator_duties: dict[str, ValidatorDuty] = {}
    if __should_fetch_attestation_duties():
        while is_any_duty_outdated:
            response_data = __fetch_duty_responses(current_epoch, DutyType.ATTESTATION)
            validator_duties = {
                data.validator_index: __get_next_attestation_duty(
                    data, validator_duties
                )
                for data in response_data
            }
            is_any_duty_outdated = [
                True for duty in validator_duties.values() if duty.slot == 0
            ]
            current_epoch += 1
    return validator_duties


def get_next_sync_committee_duties() -> dict[str, ValidatorDuty]:
    """Fetches current and upcoming sync committee duties for all validators
    provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming sync committee duties
        for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    next_sync_committee_starting_epoch = (
        ceil(current_epoch / ethereum.EPOCHS_PER_SYNC_COMMITTEE)
        * ethereum.EPOCHS_PER_SYNC_COMMITTEE
    )
    validator_duties: dict[str, ValidatorDuty] = {}
    for epoch in [current_epoch, next_sync_committee_starting_epoch]:
        response_data = __fetch_duty_responses(epoch, DutyType.SYNC_COMMITTEE)
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


def get_next_proposing_duties() -> dict[str, ValidatorDuty]:
    """Fetches upcoming block proposals for all validators which were
    provided by the user.

    Returns:
        dict[int, ValidatorDuty]: The upcoming block proposing duties
        for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    validator_duties: dict[str, ValidatorDuty] = {}
    for index in [1, 1]:
        response_data = __fetch_duty_responses(current_epoch, DutyType.PROPOSING)
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


def __should_fetch_attestation_duties() -> bool:
    """Checks if attestation duties should be fetched

    Returns:
        bool: Should attestation duties fetched
    """
    if (
        len(__VALIDATORS) > ARGUMENTS.max_attestation_duty_logs
        and not ARGUMENTS.omit_attestation_duties
    ):
        __LOGGER.warning(
            logging.TOO_MANY_PROVIDED_VALIDATORS_FOR_FETCHING_ATTESTATION_DUTIES_MESSAGE,
            ARGUMENTS.max_attestation_duty_logs,
        )
        return False
    if ARGUMENTS.omit_attestation_duties:
        return False
    return True


def __get_next_attestation_duty(
    data: ValidatorDuty, present_duties: dict[str, ValidatorDuty]
) -> ValidatorDuty:
    """Checks supplied response data for upcoming attestation duty and returns it

    Args:
        data (ValidatorDuty): Response data from rest api call
        present_duties (dict[int, ValidatorDuty]): The already fetched and processed duties

    Returns:
        ValidatorDuty: Validator duty object for the next attestation duty
    """
    current_slot = ethereum.get_current_slot()
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
    raw_proposing_duties: dict[str, ValidatorDuty]
) -> dict[str, ValidatorDuty]:
    """Filters supplied proposing duties dict for already outdated duties

    Args:
        raw_proposing_duties (dict[int, ValidatorDuty]): All fetched proposing duties
        for the current and upcoming epoch

    Returns:
        dict[int, ValidatorDuty]: Filtered proposing duties
    """
    current_slot = ethereum.get_current_slot()
    filtered_proposing_duties = {
        validator_index: proposing_duty
        for (validator_index, proposing_duty) in raw_proposing_duties.items()
        if proposing_duty.slot > current_slot
    }
    return filtered_proposing_duties


def __fetch_duty_responses(
    target_epoch: int, duty_type: DutyType
) -> List[ValidatorDuty]:
    """Fetches validator duties in dependence of the duty type from the beacon client

    Args:
        target_epoch (int): Epoch to fetch duties for
        duty_type (DutyType): Type of the duty

    Returns:
        List[ValidatorDuty]: List of fetched validator duties
    """
    match duty_type:
        case DutyType.ATTESTATION:
            responses = send_beacon_api_request(
                f"{endpoints.ATTESTATION_DUTY_ENDPOINT}{target_epoch}",
                CalldataType.REQUEST_DATA,
                __VALIDATORS,
            )
        case DutyType.SYNC_COMMITTEE:
            responses = send_beacon_api_request(
                f"{endpoints.SYNC_COMMITTEE_DUTY_ENDPOINT}{target_epoch}",
                CalldataType.REQUEST_DATA,
                __VALIDATORS,
            )
        case DutyType.PROPOSING:
            responses = send_beacon_api_request(
                f"{endpoints.BLOCK_PROPOSING_DUTY_ENDPOINT}{target_epoch}",
                CalldataType.NONE,
            )
        case _:
            responses = []
    return [ValidatorDuty.from_dict(data) for data in responses]
