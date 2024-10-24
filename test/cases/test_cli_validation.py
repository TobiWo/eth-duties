"""Module with functions to test cli validation
"""

from pathlib import Path

from test_helper.functions import run_generic_test
from test_helper.general import get_eth_duties_entry_point


def test_any_validators_flag_validation() -> int:
    """Test validators flag validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "ONE of the following flags is required: '--validators', '--validators-file', "
        "'--validator-nodes'. '--validator-nodes' can be used together with "
        "ONE of the two other flags."
    ]
    command = get_eth_duties_entry_point()
    return run_generic_test(
        expected_logs,
        command,
        "validators flag validation while providing no flag",
        "argparse.ArgumentError",
        True,
        True,
    )


def test_both_validators_flag_validation() -> int:
    """Test validators flag validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "ONE of the following flags is required: '--validators', '--validators-file', "
        "'--validator-nodes'. '--validator-nodes' can be used together with "
        "ONE of the two other flags."
    ]
    command = get_eth_duties_entry_point() + [
        "--validators",
        "1",
        "--validators-file",
        str(Path.cwd() / "test/data/devnet-validators"),
    ]
    return run_generic_test(
        expected_logs,
        command,
        "validators flag validation while providing both flags",
        "argparse.ArgumentError",
        True,
        True,
    )


def test_validator_nodes_and_validators_flag_validation() -> int:
    """Test validator-nodes and validators flag validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["All validator keymanager endpoints are healthy"]
    command = get_eth_duties_entry_point() + [
        "--validators",
        "1",
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes"),
    ]
    return run_generic_test(
        expected_logs,
        command,
        "validators flag validation while providing --validator-nodes and --validators flags",
        "Non of the provided beacon nodes is ready to accept requests",
    )


def test_validator_nodes_and_validators_file_flag_validation() -> int:
    """Test validator-nodes and validators-file flag validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["All validator keymanager endpoints are healthy"]
    command = get_eth_duties_entry_point() + [
        "--validators-file",
        str(Path.cwd() / "test/data/devnet-validators"),
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-validator-nodes"),
    ]
    return run_generic_test(
        expected_logs,
        command,
        "validators flag validation while providing --validator-nodes and --validators-file flags",
        "Non of the provided beacon nodes is ready to accept requests",
    )


def test_interval_flag_validation() -> int:
    """Test interval flag validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "The interval should be greater or equal the slot time (12 seconds)"
    ]
    command = get_eth_duties_entry_point() + ["--interval", "10"]
    return run_generic_test(
        expected_logs,
        command,
        "interval flag validation",
        "ValueError:",
        True,
        True,
    )


def test_log_time_warning_flag_validation() -> int:
    """Test log time warning validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Passed seconds for '--log-time-warning'"]
    command = get_eth_duties_entry_point() + [
        "--validators",
        "1",
        "--log-time-warning",
        "30",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "log time warning flag validation",
        "ValueError:",
        True,
        True,
    )


def test_cicd_waiting_time_flag_validation() -> int:
    """Test cicd waiting time validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["The value for flag '--mode-cicd-waiting-time' should be"]
    command = get_eth_duties_entry_point() + [
        "--validators",
        "1",
        "--mode",
        "cicd-wait",
        "--mode-cicd-waiting-time",
        "12",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd waiting time flag validation",
        "ValueError:",
        True,
        True,
    )


def test_cicd_attestation_proportion_flag_validation() -> int:
    """Test cicd attestation proportion validation

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "The value for flag '--mode-cicd-attestation-proportion' should be between 0 and 1"
    ]
    command = get_eth_duties_entry_point() + [
        "--validators",
        "1",
        "--mode",
        "cicd-wait",
        "--mode-cicd-attestation-proportion",
        "2",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd attestation proportion flag validation",
        "ValueError:",
        True,
        True,
    )
