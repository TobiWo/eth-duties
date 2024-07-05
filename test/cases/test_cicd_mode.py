"""Module with functions to test rest cicd mode
"""

# pylint: disable=line-too-long

from test_helper.config import CONFIG
from test_helper.functions import run_generic_test
from test_helper.general import get_general_eth_duties_start_command


def test_cicd_exit_mode_with_sync_committee_duties_while_proportion_of_duties_is_not_above_threshold() -> (
    int
):
    """Test cicd exit mode while proportion of duties is not above threshold

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Started in mode: cicd-exit", "Exiting with code: 1"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:10]
        + CONFIG.validators.active.in_sync_committee,
        CONFIG.general.working_beacon_node_url,
    ) + ["--mode", "cicd-exit"]
    return run_generic_test(
        expected_logs,
        command,
        "cicd exit mode with sync committee duties while proportion of duties IS NOT above threshold",
        "Exiting with code",
        drop_expected_logs=True,
    )


def test_cicd_exit_mode_without_sync_committee_duties_while_proportion_of_duties_is_not_above_threshold() -> (
    int
):
    """Test cicd exit mode while proportion of duties is not above threshold

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Started in mode: cicd-exit", "Exiting with code: 1"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.not_in_sync_committee_not_proposing,
        CONFIG.general.working_beacon_node_url,
    ) + ["--mode", "cicd-exit"]
    return run_generic_test(
        expected_logs,
        command,
        "cicd exit mode without sync committee duties while proportion of duties IS NOT above threshold",
        "Exiting with code",
        drop_expected_logs=True,
    )


def test_cicd_exit_mode_with_sync_committee_duties_while_proportion_of_attestation_duties_is_above_threshold() -> (
    int
):
    """Test cicd exit mode while proportion of duties is above threshold

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Started in mode: cicd-exit", "Exiting with code: 1"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:10]
        + CONFIG.validators.active.in_sync_committee,
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--mode",
        "cicd-exit",
        "--mode-cicd-attestation-proportion",
        "0.01",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd exit mode with sync committee duties while proportion of duties IS above threshold",
        "Exiting with code",
        drop_expected_logs=True,
    )


def test_cicd_exit_mode_without_sync_committee_duties_while_proportion_of_attestation_duties_is_above_threshold() -> (
    int
):
    """Test cicd exit mode while proportion of duties is above threshold

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["Started in mode: cicd-exit", "Exiting with code: 0"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.not_in_sync_committee_not_proposing,
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--mode",
        "cicd-exit",
        "--mode-cicd-attestation-proportion",
        "0.01",
        "--mode-cicd-attestation-time",
        "10",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd exit mode without sync committee duties while proportion of duties IS above threshold",
        "Exiting with code",
        drop_expected_logs=True,
    )


def test_cicd_force_graceful_exit_mode() -> int:
    """Test cicd force graceful exit mode

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: cicd-force-graceful-exit",
        "Exiting with code: 0",
    ]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:10], CONFIG.general.working_beacon_node_url
    ) + [
        "--mode",
        "cicd-force-graceful-exit",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd force graceful exit mode",
        "Exiting with code: 0",
        drop_expected_logs=True,
    )


def test_cicd_wait_mode_without_sync_committee_duties_while_proportion_of_duties_is_above_threshold_within_waiting_time() -> (
    int
):
    """Test cicd wait mode while proportion of duties is above threshold

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: cicd-wait",
        "Exiting with code: 0",
    ]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.not_in_sync_committee_not_proposing,
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--mode",
        "cicd-wait",
        "--mode-cicd-attestation-proportion",
        "0.01",
        "--mode-cicd-attestation-time",
        "10",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd wait mode without sync committee duties while proportion of duties IS above threshold within waiting time",
        "Exiting with code",
        drop_expected_logs=True,
    )


def test_cicd_wait_mode_while_waiting_time_exceeds() -> int:
    """Test cicd wait mode while waiting time exceeds

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: cicd-wait",
        "Reached max. waiting time for mode 'cicd-wait'",
        "Exiting with code: 1",
    ]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general[0:10]
        + CONFIG.validators.active.in_sync_committee,
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--mode",
        "cicd-wait",
        "--mode-cicd-waiting-time",
        "15",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "cicd wait mode while waiting time exceeds",
        "Exiting with code",
        drop_expected_logs=True,
    )
