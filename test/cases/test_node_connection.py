"""Module for testing node connections
"""

from pathlib import Path

from constants.logging import (
    ALL_HEALTHY_VALIDATOR_NODES_MESSAGE,
    NO_HEALTHY_VALIDATOR_NODES_MESSAGE,
    ONE_NON_HEALTHY_VALIDATOR_NODE_MESSAGE,
    VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE,
)
from test_helper.config import CONFIG
from test_helper.functions import run_generic_test
from test_helper.general import get_eth_duties_entry_point


def test_all_validator_nodes_are_healthy() -> int:
    """Test that all validator nodes are healthy

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [ALL_HEALTHY_VALIDATOR_NODES_MESSAGE]
    command = get_eth_duties_entry_point() + [
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "if all validator nodes are available",
        "Logging next duties interval",
        drop_expected_logs=True,
    )


def test_all_validator_nodes_are_healthy_with_duplicates() -> int:
    """Test that all validator nodes are healthy if duplicates in validator nodes file

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [ALL_HEALTHY_VALIDATOR_NODES_MESSAGE]
    command = get_eth_duties_entry_point() + [
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes-duplicates"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "if all validator nodes are available with duplicates in nodes file ",
        "Logging next duties interval",
        drop_expected_logs=True,
    )


def test_some_validator_nodes_are_healthy() -> int:
    """Test that some validator nodes are healthy

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        ONE_NON_HEALTHY_VALIDATOR_NODE_MESSAGE % ("http://127.0.0.1:34122")
    ]
    command = get_eth_duties_entry_point() + [
        "--validator-nodes",
        str(Path.cwd() / "test/data/some-online-validator-nodes"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "if some validator nodes are available",
        "Logging next duties interval",
        drop_expected_logs=True,
    )


def test_all_validator_nodes_are_unhealthy() -> int:
    """Test that all validator nodes are unhealthy

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [NO_HEALTHY_VALIDATOR_NODES_MESSAGE]
    command = get_eth_duties_entry_point() + [
        "--validator-nodes",
        str(Path.cwd() / "test/data/offline-validator-nodes"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "if all validator nodes are NOT available",
        "Logging next duties interval",
        drop_expected_logs=True,
    )


def test_wrong_bearer_token_for_authentication() -> int:
    """Test incorrect authentication

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE % ("http://127.0.0.1:34013")
    ]
    command = get_eth_duties_entry_point() + [
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-and-wrong-auth-validator-nodes"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "incorrect validator node authentication",
        "Logging next duties interval",
        drop_expected_logs=True,
    )
