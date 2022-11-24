"""Module which holds all logic for fetching validator duties
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
from fetcher.data_types import ValidatorDuty, DutyType
from fetcher.constants import ethereum
from fetcher.constants import endpoints
from fetcher.constants import json
from fetcher.constants import logging
from fetcher.constants import program


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
        return trunc((time() - self.genesis_time) / ethereum.SLOT_TIME)

    def get_next_attestation_duties(self) -> dict[int, ValidatorDuty]:
        """Fetches upcoming attestations (for current and upcoming epoch)
        for all validators which were provided during class instantiation.

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
        """Fetches raw responses for provided duties

        Args:
            target_epoch (int): Epoch to check for duties
            duty_type (DutyType): Type of the duty
            request_data (str, optional): Request data if any are present. Defaults to "".

        Returns:
            List[ValidatorDuty]: List of all fetched validator duties for a specific epoch
        """
        response = self.__fetch_duty_response(target_epoch, duty_type, request_data)
        response_data = response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME]
        return [ValidatorDuty.from_dict(data) for data in response_data]

    def __get_current_epoch(self) -> int:
        """Calculates the current epoch based on connected chain specifics

        Returns:
            int: Current epoch
        """
        now = time()
        return trunc(
            (now - self.genesis_time) / (ethereum.SLOTS_PER_EPOCH * ethereum.SLOT_TIME)
        )

    def __get_next_attestation_duty(
        self, data: ValidatorDuty, present_duties: dict[int, ValidatorDuty]
    ) -> ValidatorDuty:
        """Checks supplied response data for upcoming attestation duty and returns it

        Args:
            data (ValidatorDuty): Response data from rest api call
            present_duties (dict[int, ValidatorDuty]): The already fetched and processed duties

        Returns:
            ValidatorDuty: Validator duty object for the next attestation duty
        """
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
        """Filters supplied proposing duties dict for already outdated duties

        Args:
            raw_proposing_duties (dict[int, ValidatorDuty]): All fetched proposing duties
            for the current and upcoming epoch

        Returns:
            dict[int, ValidatorDuty]: Filtered proposing duties
        """
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
                response = self.__send_beacon_api_request(
                    f"{endpoints.ATTESTATION_DUTY_ENDPOINT}{target_epoch}", request_data
                )
            case DutyType.PROPOSING:
                response = self.__send_beacon_api_request(
                    f"{endpoints.BLOCK_PROPOSING_DUTY_ENDPOINT}{target_epoch}"
                )
        return response

    def __fetch_genesis_time(self) -> int:
        """Fetches the genesis time from the beacon client

        Returns:
            int: Genesis time as unix timestamp in seconds
        """
        response = self.__send_beacon_api_request(endpoints.BEACON_GENESIS_ENDPOINT)
        return int(
            response.json()[json.RESPONSE_JSON_DATA_FIELD_NAME][
                json.RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME
            ]
        )

    def __send_beacon_api_request(
        self, endpoint: str, request_data: str = ""
    ) -> Response:
        """Sends an api request to the beacon client

        Args:
            endpoint (str): The endpoint which will be called
            request_data (str, optional): Request data if any. Defaults to "".

        Raises:
            SystemExit: Program exit if the response is not present at all
            which will happen if the user interrupts at specific moment during
            execution

        Returns:
            Response: Response object with data provided by the endpoint
        """
        is_request_successful = False
        response = None
        while not is_request_successful and not self.__graceful_killer.kill_now:
            try:
                if len(request_data) == 0:
                    response = get(
                        url=f"{self.__beacon_node_url}{endpoint}",
                        timeout=program.REQUEST_TIMEOUT,
                    )
                else:
                    response = post(
                        url=f"{self.__beacon_node_url}{endpoint}",
                        data=request_data,
                        timeout=program.REQUEST_TIMEOUT,
                    )
                response.close()
                is_request_successful = self.__is_request_successful(response)
            except RequestsConnectionError:
                self.__logger.error(logging.CONNECTION_ERROR_MESSAGE)
                sleep(program.REQUEST_CONNECTION_ERROR_WAITING_TIME)
            except (ReadTimeout, KeyError):
                self.__logger.error(logging.READ_TIMEOUT_ERROR_MESSAGE)
                sleep(program.REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME)
        if response:
            return response
        self.__logger.error(logging.SYSTEM_EXIT_MESSAGE)
        raise SystemExit()

    def __is_request_successful(self, response: Response) -> bool:
        """Helper to check if a request was successful

        Args:
            response (Response): Response object from the api call

        Raises:
            RuntimeError: Raised when reponse is totally empty
            KeyError: Raised if no data field is within the response object

        Returns:
            bool: True if request was successful
        """
        if not response.text:
            raise RuntimeError(logging.NO_RESPONSE_ERROR_MESSAGE)
        if json.RESPONSE_JSON_DATA_FIELD_NAME in response.json():
            return True
        raise KeyError(logging.NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE)
