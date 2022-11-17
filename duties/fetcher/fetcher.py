"""
Module which holds all logic for fetching and printing validator duties
"""

# pylint: disable=import-error

from time import time, sleep
from math import trunc
from typing import List
from logging import getLogger
from requests import (
    post,
    get,
    Response,
    ConnectionError as RequestsConnectionError,
    ReadTimeout,
)
from helper.killer import GracefulKiller
from .data_types import ValidatorDuty, DutyType
from .constants import (
    SLOT_TIME,
    SLOTS_PER_EPOCH,
    ATTESTATION_DUTY_ENDPOINT,
    BLOCK_PROPOSING_DUTY_ENDPOINT,
    BEACON_GENESIS_ENDPOINT,
    RESPONSE_JSON_DATA_FIELD_NAME,
    RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME,
    REQUEST_TIMEOUT,
    REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME,
    REQUEST_CONNECTION_ERROR_WAITING_TIME,
    CONNECTION_ERROR_MESSAGE,
    READ_TIMEOUT_ERROR_MESSAGE,
    NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE,
    NO_RESPONSE_ERROR_MESSAGE,
)


class ValidatorDutyFetcher:
    """
    Class which holds all logic for fetching validator duties
    """

    def __init__(
        self,
        beacon_node_url: str,
        validators: List[str],
        graceful_killer: GracefulKiller,
    ) -> None:
        self.__logger = getLogger(__name__)
        self.__beacon_node_url = beacon_node_url
        self.__validators = validators
        self.__graceful_killer = graceful_killer
        self.genesis_time = self.__fetch_genesis_time()

    def get_current_slot(self) -> int:
        """
        Calculates the current beacon chain slot

        Returns:
            int: The current beacon chain slot
        """
        return trunc((time() - self.genesis_time) / SLOT_TIME)

    def get_next_attestation_duties(self) -> dict[int, ValidatorDuty]:
        """
        Fetches upcoming attestations for all validators which were
        provided during class instantiation.

        Returns:
            dict[int, ValidatorDuty]: The upcoming attestation duties
            for all provided validators
        """
        target_epoch = self.__get_current_epoch()
        request_data = f"[{','.join(self.__validators)}]"
        is_any_duty_outdated: List[bool] = [True]
        validator_duties: dict[int, ValidatorDuty] = {}
        while is_any_duty_outdated:
            response_data = self.__get_raw_response_data(
                target_epoch, DutyType.ATTESTATION, request_data
            )
            validator_duties = {
                data.validator_index: self.__get_next_attestation_duty(
                    data, validator_duties
                )
                for data in response_data
            }
            is_any_duty_outdated = [
                True for duty in validator_duties.values() if duty.slot == 0
            ]
            target_epoch += 1
        return validator_duties

    def get_next_proposing_duties(self) -> dict[int, ValidatorDuty]:
        """
        Fetches upcoming block proposals for all validators which were
        provided during class instantiation.

        Returns:
            dict[int, ValidatorDuty]: The upcoming block proposing duties
            for all provided validators
        """
        target_epoch = self.__get_current_epoch()
        validator_duties: dict[int, ValidatorDuty] = {}
        for index in [1, 1]:
            response_data = self.__get_raw_response_data(
                target_epoch, DutyType.PROPOSING
            )
            for data in response_data:
                if (
                    str(data.validator_index) in self.__validators
                    and data.validator_index not in validator_duties
                ):
                    validator_duties[data.validator_index] = ValidatorDuty(
                        data.pubkey,
                        data.validator_index,
                        data.slot,
                        DutyType.PROPOSING,
                    )
            target_epoch += index
        return self.__filter_proposing_duties(validator_duties)

    def __get_raw_response_data(
        self, target_epoch: int, duty_type: DutyType, request_data: str = ""
    ) -> List[ValidatorDuty]:
        response = self.__fetch_duty_response(target_epoch, duty_type, request_data)
        response_data = response.json()[RESPONSE_JSON_DATA_FIELD_NAME]
        return [ValidatorDuty.from_dict(data) for data in response_data]

    def __get_current_epoch(self) -> int:
        now = time()
        return trunc((now - self.genesis_time) / (SLOTS_PER_EPOCH * SLOT_TIME))

    def __get_next_attestation_duty(
        self, data: ValidatorDuty, present_duties: dict[int, ValidatorDuty]
    ) -> ValidatorDuty:
        current_slot = self.get_current_slot()
        if data.validator_index in present_duties:
            present_validator_duty = present_duties[data.validator_index]
            if present_validator_duty.slot != 0:
                return present_validator_duty
        attestation_duty = ValidatorDuty(
            data.pubkey, data.validator_index, 0, DutyType.ATTESTATION
        )
        if current_slot >= data.slot:
            return attestation_duty
        attestation_duty.slot = data.slot
        return attestation_duty

    def __filter_proposing_duties(
        self, raw_proposing_duties: dict[int, ValidatorDuty]
    ) -> dict[int, ValidatorDuty]:
        current_slot = self.get_current_slot()
        filtered_proposing_duties = {
            validator_index: proposing_duty
            for (validator_index, proposing_duty) in raw_proposing_duties.items()
            if proposing_duty.slot > current_slot
        }
        return filtered_proposing_duties

    def __fetch_duty_response(
        self, target_epoch: int, duty_type: DutyType, request_data: str = ""
    ) -> Response:
        match duty_type:
            case DutyType.ATTESTATION:
                response = self.__send_beacon_api_request(
                    f"{ATTESTATION_DUTY_ENDPOINT}{target_epoch}", request_data
                )
            case DutyType.PROPOSING:
                response = self.__send_beacon_api_request(
                    f"{BLOCK_PROPOSING_DUTY_ENDPOINT}{target_epoch}"
                )
        return response

    def __fetch_genesis_time(self) -> int:
        response = self.__send_beacon_api_request(BEACON_GENESIS_ENDPOINT)
        return int(
            response.json()[RESPONSE_JSON_DATA_FIELD_NAME][
                RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME
            ]
        )

    def __send_beacon_api_request(
        self, endpoint: str, request_data: str = ""
    ) -> Response:
        is_request_successful = False
        response = None
        while not is_request_successful and not self.__graceful_killer.kill_now:
            try:
                if len(request_data) == 0:
                    response = get(
                        url=f"{self.__beacon_node_url}{endpoint}",
                        timeout=REQUEST_TIMEOUT,
                    )
                else:
                    response = post(
                        url=f"{self.__beacon_node_url}{endpoint}",
                        data=request_data,
                        timeout=REQUEST_TIMEOUT,
                    )
                response.close()
                is_request_successful = self.__is_request_successful(response)
            except RequestsConnectionError:
                self.__logger.error(CONNECTION_ERROR_MESSAGE)
                sleep(REQUEST_CONNECTION_ERROR_WAITING_TIME)
            except ReadTimeout:
                self.__logger.error(READ_TIMEOUT_ERROR_MESSAGE)
                sleep(REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME)
        if response:
            return response
        self.__logger.error("Detected user intervention (SIGINT). Stopping program.")
        raise SystemExit()

    def __is_request_successful(self, response: Response) -> bool:
        if not response.text:
            raise RuntimeError(NO_RESPONSE_ERROR_MESSAGE)
        if RESPONSE_JSON_DATA_FIELD_NAME in response.json():
            return True
        raise KeyError(NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE)
