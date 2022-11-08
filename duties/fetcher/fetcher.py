"""
Module which holds all logic for fetching and printing validator duties
"""

# pylint: disable=import-error

from time import time, sleep
from math import trunc
from typing import List
from sys import exit as sys_exit
from requests import (
    post,
    get,
    Response,
    ConnectionError as RequestsConnectionError,
    ReadTimeout,
)
from helper.killer import GracefulKiller
from .data_types import RawValidatorDuty, ValidatorDuty, DutyType


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
        return trunc((time() - self.genesis_time) / 12)

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
            if response_data:
                validator_duties = {
                    data.validator_index: self.__get_next_attestation_duty(
                        data, validator_duties
                    )
                    for data in response_data
                }
                is_any_duty_outdated = [
                    True for duty in validator_duties.values() if duty.target_slot == 0
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
            if response_data:
                for data in response_data:
                    if (
                        str(data.validator_index) in self.__validators
                        and data.validator_index not in validator_duties
                    ):
                        validator_duties[data.validator_index] = ValidatorDuty(
                            data.validator_index, data.slot, DutyType.PROPOSING
                        )
                target_epoch += index
        return self.__filter_proposing_duties(validator_duties)

    def __fetch_genesis_time(self) -> int:
        response = self.__send_beacon_api_request("/eth/v1/beacon/genesis")
        if not response.text:
            sys_exit("Exited")  # besser
        return int(response.json()["data"]["genesis_time"])

    def __send_beacon_api_request(
        self, endpoint: str, request_data: str = ""
    ) -> Response:
        is_request_successful = False
        response: Response = Response()
        while not is_request_successful and not self.__graceful_killer.kill_now:
            try:
                if len(request_data) == 0:
                    response = get(
                        url=f"{self.__beacon_node_url}{endpoint}", timeout=(3, 5)
                    )
                else:
                    response = post(
                        url=f"{self.__beacon_node_url}{endpoint}",
                        data=request_data,
                        timeout=(3, 5),
                    )
                response.close()
                if "data" in response.json():
                    is_request_successful = True
            except RequestsConnectionError:
                print("Couldn't connect to beacon client. Retry in 2 second.")
                sleep(2)
            except ReadTimeout:
                print("Couldn't read from beacon client. Retry in 5 seconds.")
                sleep(5)
        return response

    def __get_current_epoch(self) -> int:
        now = time()
        return trunc((now - self.genesis_time) / (32 * 12))

    def __get_next_attestation_duty(
        self, data: RawValidatorDuty, present_duties: dict[int, ValidatorDuty]
    ) -> ValidatorDuty:
        current_slot = self.get_current_slot()
        if data.validator_index in present_duties:
            present_validator_duty = present_duties[data.validator_index]
            if present_validator_duty.target_slot != 0:
                return present_validator_duty
        attestation_duty = ValidatorDuty(data.validator_index, 0, DutyType.ATTESTATION)
        if current_slot >= data.slot:
            return attestation_duty
        attestation_duty.target_slot = data.slot
        return attestation_duty

    def __filter_proposing_duties(
        self, raw_proposing_duties: dict[int, ValidatorDuty]
    ) -> dict[int, ValidatorDuty]:
        current_slot = self.get_current_slot()
        filtered_proposing_duties = {
            validator_index: proposing_duty
            for (validator_index, proposing_duty) in raw_proposing_duties.items()
            if proposing_duty.target_slot > current_slot
        }
        return filtered_proposing_duties

    def __get_raw_response_data(
        self, target_epoch: int, duty_type: DutyType, request_data: str = ""
    ) -> List[RawValidatorDuty] | None:
        # is_request_successful = False
        # Logik für leeres data objekt in der response Objekt überarbeiten
        # None Logik überarbeiten (generell in Klasse)
        # response: Response = Response()
        # while not is_request_successful:
        # try:
        response = self.__fetch_duty_response(target_epoch, duty_type, request_data)
        response_data = response.json()["data"]
        if response_data:
            # if "data" in response.json():
            #     is_request_successful = True
            # except RequestsConnectionError:
            #     print("Couldn't connect to beacon client. Retry in 2 seconds.")
            #     sleep(2)
            # except ReadTimeout:
            #     print("Couldn't read from beacon client. Retry in 5 seconds.")
            #     sleep(5)
            return [RawValidatorDuty.from_dict(data) for data in response_data]
        return None

    def __fetch_duty_response(
        self, target_epoch: int, duty_type: DutyType, request_data: str = ""
    ) -> Response:
        match duty_type:
            case DutyType.ATTESTATION:
                response = self.__send_beacon_api_request(
                    f"/eth/v1/validator/duties/attester/{target_epoch}", request_data
                )
            case DutyType.PROPOSING:
                response = self.__send_beacon_api_request(
                    f"/eth/v1/validator/duties/proposer/{target_epoch}"
                )
        return response
