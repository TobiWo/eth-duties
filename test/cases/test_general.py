"""Module with functions to test eth-duties startup
"""

from pathlib import Path

# pylint: disable-next=import-error
from constants.logging import (
    CONNECTION_ERROR_MESSAGE,
    LOADED_VALIDATOR_IDENTIFIER_MESSAGE,
    NEXT_INTERVAL_MESSAGE,
    NO_AVAILABLE_BEACON_NODE_MESSAGE,
    UPDATE_VALIDATOR_IDENTIFIER_MESSAGE,
)
from test_helper.config import CONFIG
from test_helper.functions import run_generic_test
from test_helper.general import (
    get_eth_duties_entry_point,
    get_general_eth_duties_start_command,
)


def test_no_beacon_connection_at_startup() -> int:
    """Test no present beacon node connection at startup

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        CONNECTION_ERROR_MESSAGE % ("beacon", CONFIG.general.failing_beacon_node_url),
        NO_AVAILABLE_BEACON_NODE_MESSAGE,
    ]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general, CONFIG.general.failing_beacon_node_url
    )
    return run_generic_test(
        expected_logs, command, "no beacon connection at startup", expected_logs[0]
    )


def test_scheduled_validator_identifier_update_from_validator_nodes() -> int:
    """Test scheduled validator identifier update

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [UPDATE_VALIDATOR_IDENTIFIER_MESSAGE]
    command = get_eth_duties_entry_point() + [
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes"),
        "--validator-update-interval",
        "1",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "validator identifier update interval ",
        UPDATE_VALIDATOR_IDENTIFIER_MESSAGE,
    )


def test_number_of_fetched_validator_identifiers_from_validator_nodes() -> int:
    """Test number of fetched validator identifiers. Needs to be adapted
    if kurtosis testnet is changed.

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [LOADED_VALIDATOR_IDENTIFIER_MESSAGE % (151)]
    command = get_eth_duties_entry_point() + [
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes"),
    ]
    return run_generic_test(
        expected_logs,
        command,
        "number of fetched validator identifiers",
        NEXT_INTERVAL_MESSAGE,
    )
