"""Module which holds all logic for fetching validator duties"""

from typing import List, Literal, Tuple, Type, TypeVar

from cli.arguments import ARGUMENTS
from constants import endpoints, program
from fetcher.data_types import (
    AttestationDuty,
    DutyType,
    ProposingDuty,
    PtcDuty,
    SlotBasedDuty,
    SyncCommitteeDuty,
    ValidatorDuty,
)
from fetcher.identifier import core
from helper.error import NoDataFromEndpointError
from protocol import ethereum
from protocol.request import CalldataType, send_beacon_api_request

__VALIDATOR_IDENTIFIER_CACHE: List[str] = []

SlotBasedDutyT = TypeVar("SlotBasedDutyT", bound=SlotBasedDuty)
ValidatorDutyT = TypeVar("ValidatorDutyT", bound=ValidatorDuty)

DUTY_REQUEST_PROPERTIES: dict[DutyType, Tuple[str, CalldataType]] = {
    DutyType.ATTESTATION: (
        endpoints.ATTESTATION_DUTY_ENDPOINT,
        CalldataType.REQUEST_DATA,
    ),
    DutyType.SYNC_COMMITTEE: (
        endpoints.SYNC_COMMITTEE_DUTY_ENDPOINT,
        CalldataType.REQUEST_DATA,
    ),
    DutyType.PROPOSING: (
        endpoints.BLOCK_PROPOSING_DUTY_ENDPOINT,
        CalldataType.NONE,
    ),
    DutyType.PTC: (endpoints.PTC_DUTY_ENDPOINT, CalldataType.REQUEST_DATA),
}


def update_validator_identifier_cache() -> None:
    """Updates the validator identifiers for the fetch module"""
    complete_active_validator_identifiers = (
        core.read_validator_identifiers_from_shared_memory(
            program.ACTIVE_VALIDATOR_IDENTIFIERS_SHARED_MEMORY_NAME
        )
    )
    __VALIDATOR_IDENTIFIER_CACHE.clear()
    __VALIDATOR_IDENTIFIER_CACHE.extend(
        list(complete_active_validator_identifiers.keys())
    )


def get_validator_count() -> int:
    """Returns the number of validators in the cache.

    Returns:
        int: Number of cached validator identifiers
    """
    return len(__VALIDATOR_IDENTIFIER_CACHE)


async def fetch_upcoming_attestation_duties() -> dict[str, AttestationDuty]:
    """Fetches upcoming attestations (for current and upcoming epoch)
    for all validators which were provided by the user.

    Returns:
        dict[str, AttestationDuty]: The upcoming attestation duties for all provided validators
    """
    return await __fetch_upcoming_slot_based_duties(
        DutyType.ATTESTATION, AttestationDuty
    )


async def fetch_upcoming_ptc_duties() -> dict[str, PtcDuty]:
    """Fetches upcoming payload timeliness committee duties (for current and
    upcoming epoch) for all validators which were provided by the user.

    Returns:
        dict[str, PtcDuty]: The upcoming ptc duties for all provided validators
    """
    return await __fetch_upcoming_slot_based_duties(DutyType.PTC, PtcDuty)


async def fetch_upcoming_sync_committee_duties() -> dict[str, SyncCommitteeDuty]:
    """Fetches current and upcoming sync committee duties for all validators
    provided by the user.

    Returns:
        dict[str, SyncCommitteeDuty]: The upcoming sync committee duties for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    current_sync_committee_epoch_boundaries = (
        ethereum.get_sync_committee_epoch_boundaries(current_epoch)
    )
    validator_duties: dict[str, SyncCommitteeDuty] = {}
    if __should_fetch_duties(DutyType.SYNC_COMMITTEE):
        for epoch in [current_epoch, (current_sync_committee_epoch_boundaries[1] + 1)]:
            response_data = await __fetch_duty_responses(
                epoch, DutyType.SYNC_COMMITTEE, SyncCommitteeDuty
            )
            for data in response_data:
                if data.validator_index not in validator_duties:
                    sync_committee_duty = SyncCommitteeDuty(
                        pubkey=data.pubkey,
                        validator_index=data.validator_index,
                        epoch=epoch,
                        validator_sync_committee_indices=data.validator_sync_committee_indices,
                        type=DutyType.SYNC_COMMITTEE,
                    )
                    ethereum.set_time_to_duty(sync_committee_duty)
                    validator_duties[data.validator_index] = sync_committee_duty
    return validator_duties


async def fetch_upcoming_proposing_duties() -> dict[str, ProposingDuty]:
    """Fetches upcoming block proposals for all validators which were
    provided by the user.

    Returns:
        dict[str, ProposingDuty]: The upcoming block proposing duties for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    validator_duties: dict[str, ProposingDuty] = {}
    for index in [1, 1]:
        response_data = await __fetch_duty_responses(
            current_epoch, DutyType.PROPOSING, ProposingDuty
        )
        for data in response_data:
            if (
                str(data.validator_index) in __VALIDATOR_IDENTIFIER_CACHE
                and data.validator_index not in validator_duties
            ):
                proposing_duty = ProposingDuty(
                    pubkey=data.pubkey,
                    validator_index=data.validator_index,
                    slot=data.slot,
                    type=DutyType.PROPOSING,
                )
                ethereum.set_time_to_duty(proposing_duty)
                validator_duties[data.validator_index] = proposing_duty
        current_epoch += index
    return __filter_proposing_duties(validator_duties)


async def __fetch_upcoming_slot_based_duties(
    duty_type: Literal[DutyType.ATTESTATION, DutyType.PTC],
    duty_class: Type[SlotBasedDutyT],
) -> dict[str, SlotBasedDutyT]:
    """Fetches upcoming slot based duties for the current and upcoming epoch

    Both attestation and ptc duties are assigned per slot and are fetched for the
    current epoch first. If any validator has no duty left in that epoch the next
    epoch is fetched as well.

    Args:
        duty_type (Literal[DutyType.ATTESTATION, DutyType.PTC]): Type of the duty to fetch
        duty_class (Type[SlotBasedDutyT]): Duty class which will be instantiated

    Returns:
        dict[str, SlotBasedDutyT]: The upcoming duties for all provided validators
    """
    current_epoch = ethereum.get_current_epoch()
    is_any_duty_outdated: List[bool] = [True]
    validator_duties: dict[str, SlotBasedDutyT] = {}
    if __should_fetch_duties(duty_type):
        while is_any_duty_outdated:
            response_data = await __fetch_duty_responses(
                current_epoch, duty_type, duty_class
            )
            validator_duties = {
                data.validator_index: __get_next_slot_based_duty(
                    data, validator_duties, duty_type, duty_class
                )
                for data in response_data
            }
            is_any_duty_outdated = [
                True for duty in validator_duties.values() if duty.slot == 0
            ]
            current_epoch += 1
    return validator_duties


async def __fetch_duty_responses(
    target_epoch: int, duty_type: DutyType, duty_class: Type[ValidatorDutyT]
) -> List[ValidatorDutyT]:
    """Fetches validator duties in dependence of the duty type from the beacon client

    Endpoint and calldata type per duty type are defined in DUTY_REQUEST_PROPERTIES.
    Validator identifiers are only submitted for endpoints which accept a request
    body. The block proposing endpoint returns all validators of the network and
    therefore needs to be filtered by the caller.

    Args:
        target_epoch (int): Epoch to fetch duties for
        duty_type (DutyType): Type of the duty
        duty_class (Type[ValidatorDutyT]): Duty class which will be instantiated

    Returns:
        List[ValidatorDutyT]: List of fetched validator duties
    """
    endpoint, calldata_type = DUTY_REQUEST_PROPERTIES[duty_type]
    try:
        responses = await send_beacon_api_request(
            f"{endpoint}{target_epoch}",
            calldata_type,
            (
                __VALIDATOR_IDENTIFIER_CACHE
                if calldata_type is CalldataType.REQUEST_DATA
                else None
            ),
        )
        return [duty_class.model_validate(data) for data in responses]
    except NoDataFromEndpointError:
        return []


def __should_fetch_duties(duty_type: DutyType) -> bool:
    """Checks if duties of a specific type should be fetched

    Args:
        duty_type (DutyType): Type of the duty to check for

    Returns:
        bool: Should duties be fetched
    """
    match duty_type:
        case DutyType.ATTESTATION:
            return not ARGUMENTS.omit_attestation_duties
        case DutyType.SYNC_COMMITTEE:
            return not ARGUMENTS.omit_sync_committee_duties
        case DutyType.PTC:
            return not ARGUMENTS.omit_ptc_duties and ethereum.is_gloas_active()
        case _:
            return True


def __get_next_slot_based_duty(
    data: SlotBasedDuty,
    present_duties: dict[str, SlotBasedDutyT],
    duty_type: DutyType,
    duty_class: Type[SlotBasedDutyT],
) -> SlotBasedDutyT:
    """Checks supplied response data for the next upcoming slot based duty and returns it

    Args:
        data (SlotBasedDuty): Response data from rest api call
        present_duties (dict[str, SlotBasedDutyT]): The already fetched and processed duties
        duty_type (DutyType): Type of the duty
        duty_class (Type[SlotBasedDutyT]): Duty class which will be instantiated

    Returns:
        SlotBasedDutyT: Validator duty object for the next upcoming duty
    """
    current_slot = ethereum.get_current_slot()
    if data.validator_index in present_duties:
        present_validator_duty = present_duties[data.validator_index]
        if present_validator_duty.slot != 0:
            return present_validator_duty
    validator_duty = duty_class(
        pubkey=data.pubkey,
        validator_index=data.validator_index,
        type=duty_type,
    )
    if current_slot >= data.slot:
        return validator_duty
    validator_duty.slot = data.slot
    ethereum.set_time_to_duty(validator_duty)
    return validator_duty


def __filter_proposing_duties(
    raw_proposing_duties: dict[str, ProposingDuty],
) -> dict[str, ProposingDuty]:
    """Filters supplied proposing duties dict for already outdated duties

    Args:
        raw_proposing_duties (dict[str, ProposingDuty]): All fetched proposing duties for the current and upcoming epoch # pylint: disable=line-too-long

    Returns:
        dict[str, ProposingDuty]: Filtered proposing duties
    """
    current_slot = ethereum.get_current_slot()
    filtered_proposing_duties = {
        validator_index: proposing_duty
        for (validator_index, proposing_duty) in raw_proposing_duties.items()
        if proposing_duty.slot > current_slot
    }
    return filtered_proposing_duties
