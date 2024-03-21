"""Module with functions to test rest api
"""

from typing import Any

# pylint: disable-next=import-error
from constants.program import REQUEST_TIMEOUT
from requests import delete, get, post
from test_helper.config import CONFIG
from test_helper.functions import run_generic_test
from test_helper.general import get_general_eth_duties_start_command


def get_attestation_duties_rest_call() -> Any:
    """Get attestation duties rest call

    Returns:
        Any: Rest call response
    """
    return get(
        f"http://localhost:{CONFIG.general.rest_port}/duties/raw/attestation",
        timeout=REQUEST_TIMEOUT,
    )


def test_rest_while_running_in_cicd_mode() -> int:
    """Test rest in cicd mode

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Rest server will not be started in any cicd-mode"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:3], CONFIG.general.working_beacon_node_url
    ) + [
        "--rest",
        "--mode",
        "cicd-exit",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "rest while running in cicd mode",
        "Rest server will not be started in any cicd-mode",
    )


def test_get_attestation_duties_from_rest_endpoint() -> int:
    """Test rest api get attestion duties endpoint

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    expected_logs = [
        "Validator 1 has next ATTESTATION duty",
        "Validator 2 has next ATTESTATION duty",
        "Validator 3 has next ATTESTATION duty",
    ]
    command = command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:3], CONFIG.general.working_beacon_node_url
    ) + ["--rest", "--rest-port", CONFIG.general.rest_port]
    return run_generic_test(
        expected_logs,
        command,
        "get attestation duties from rest endpoint",
        "GET /duties/raw/attestation",
        rest_call=get_attestation_duties_rest_call,
        rest_call_trigger_log="all duties will be executed in",
    )


def test_get_sync_committee_duties_from_rest_endpoint() -> int:
    """Test rest api get sync committee duties endpoint

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    def get_sync_committee_duties_rest_call() -> Any:
        """Get sync committee duties rest call

        Returns:
            Any: Rest call response
        """
        return get(
            "http://localhost:5000/duties/raw/sync-committee", timeout=REQUEST_TIMEOUT
        )

    expected_logs = [
        f"Validator {validator} is in current sync committee"
        for validator in CONFIG.validators.active.in_sync_committee
    ] + [
        f"Validator {validator} will be in next sync committee"
        for validator in CONFIG.validators.active.next_sync_committee
    ]
    command = command = get_general_eth_duties_start_command(
        CONFIG.validators.active.in_sync_committee
        + CONFIG.validators.active.next_sync_committee,
        CONFIG.general.working_beacon_node_url,
    ) + ["--rest"]
    return run_generic_test(
        expected_logs,
        command,
        "get sync committee duties from rest endpoint",
        "GET /duties/raw/sync-committee",
        rest_call=get_sync_committee_duties_rest_call,
        rest_call_trigger_log="all duties will be executed in",
        additional_failure_message=(
            "Please check if provided validators still have sync committee duties in the queue."
        ),
    )


def test_get_block_proposing_duties_from_rest_endpoint() -> int:
    """Test rest api get block proposing duties endpoint

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    def get_block_proposing_duties_rest_call() -> Any:
        """Get block proposing duties rest call

        Returns:
            Any: Rest call response
        """
        return get(
            "http://localhost:5000/duties/raw/proposing", timeout=REQUEST_TIMEOUT
        )

    expected_logs = [
        f"Validator {validator} has next PROPOSING duty in"
        for validator in CONFIG.validators.active.proposing_blocks
    ]
    command = command = get_general_eth_duties_start_command(
        CONFIG.validators.active.proposing_blocks,
        CONFIG.general.working_beacon_node_url,
    ) + ["--rest"]
    return run_generic_test(
        expected_logs,
        command,
        "get block proposing duties from rest endpoint",
        "GET /duties/raw/proposing",
        rest_call=get_block_proposing_duties_rest_call,
        rest_call_trigger_log="all duties will be executed in",
        additional_failure_message=(
            "Please check if provided validators still have proposing duties in the queue. "
            "The recommendation is to get farthest proposing duty via beacon node call to "
            "'http://localhost:5051/eth/v1/validator/duties/proposer/<CURRENT_EPOCH>+1'"
        ),
    )


def test_post_new_validator_identifier_rest_endpoint() -> int:
    """Test rest api add validator index endpoint

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    def post_validator_identifier_rest_call() -> Any:
        """Post validator identifier rest call

        Returns:
            Any: Rest call response
        """
        return post(
            "http://localhost:5000/validator/identifier",
            data='["3", "4", "5"]',
            headers={"Content-type": "application/json", "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )

    expected_logs = ["POST validator identifiers: ['3', '4', '5']"] + [
        f"Validator {validator} has next ATTESTATION duty in"
        for validator in CONFIG.validators.active.general[0:5]
    ]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:3],
        CONFIG.general.working_beacon_node_url,
    ) + ["--rest"]
    return run_generic_test(
        expected_logs,
        command,
        "post new validator identifiers via rest endpoint",
        "Validator 5 has next ATTESTATION duty in",
        drop_expected_logs=True,
        rest_call=post_validator_identifier_rest_call,
        rest_call_trigger_log="all duties will be executed in",
        test_rest_response_length=False,
        overhead_log_number=10,
    )


def test_delete_validator_identifier_rest_endpoint() -> int:
    """Test rest api delete validator index endpoint

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    def delete_validator_identifier_rest_call() -> Any:
        """Delete validator identifier rest call

        Returns:
            Any: Rest call response
        """
        return delete(
            "http://localhost:5000/validator/identifier",
            data='["4", "5"]',
            headers={"Content-type": "application/json", "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )

    expected_logs = ["DELETE validator identifiers: ['4', '5']"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:5],
        CONFIG.general.working_beacon_node_url,
    ) + ["--rest"]
    return run_generic_test(
        expected_logs,
        command,
        "delete validator identifiers via rest endpoint",
        "DELETE validator identifiers",
        rest_call=delete_validator_identifier_rest_call,
        rest_call_trigger_log="Logging next duties interval",
        test_rest_response_length=False,
    )


def test_start_rest_api_on_different_port() -> int:
    """Test starting rest api on different port

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    expected_logs = [
        f"Started rest api server on localhost:{CONFIG.general.rest_port}",
        "Validator 1 has next ATTESTATION duty",
        "Validator 2 has next ATTESTATION duty",
        "Validator 3 has next ATTESTATION duty",
    ]
    command = command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:3], CONFIG.general.working_beacon_node_url
    ) + ["--rest", "--rest-port", CONFIG.general.rest_port]
    return run_generic_test(
        expected_logs,
        command,
        "start rest api on different port",
        "GET /duties/raw/attestation",
        rest_call=get_attestation_duties_rest_call,
        rest_call_trigger_log="all duties will be executed in",
        test_rest_response_length=False,
    )


def test_start_rest_api_on_port_in_usage() -> int:
    """Test starting rest api on a port which is already in usage/blocked

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """

    expected_logs = [
        f"Port {CONFIG.general.rest_port_in_usage} is already in use. Starting eth-duties without rest server."
    ]
    command = command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:3], CONFIG.general.working_beacon_node_url
    ) + ["--rest", "--rest-port", CONFIG.general.rest_port_in_usage]
    return run_generic_test(
        expected_logs,
        command,
        "start rest api on a port in usage",
        "Starting eth-duties without rest server",
    )
