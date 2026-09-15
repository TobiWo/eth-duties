"""Module with functions to test logging mode"""

from pathlib import Path

from sty import fg  # type: ignore[import]
from test_helper.chain import get_validators_with_ptc_duty
from test_helper.config import CONFIG, ETH_DUTIES_ENTRY_POINT
from test_helper.functions import (
    run_generic_test,
    skip_test,
    test_set_colorful_logging_thresholds,
    test_standard_logging_mode,
    test_time_to_next_sync_committee_format,
)
from test_helper.general import (
    get_eth_duties_entry_point,
    get_general_eth_duties_start_command,
)


def test_standard_logging_mode_execution() -> int:
    """Test for active and inactive validators supplied as index or pubkey
    as well as for duplicates in general

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "next ATTESTATION duty",
        "next PROPOSING duty",
        "next PTC duty",
        "is in current sync committee",
    ]
    validators_to_test = (
        CONFIG.validators.active.general[0:10]
        + CONFIG.validators.inactive
        + CONFIG.validators.active.general[0:5]
    )
    command = get_general_eth_duties_start_command(
        validators_to_test, CONFIG.general.working_beacon_node_url
    )
    try:
        test_standard_logging_mode(
            command, "duties will be executed", expected_logs, validators_to_test
        )
        return 1
    except AssertionError:
        print(fg.red + "Test Failed" + fg.rs)
        print(
            fg.red + "It is possible that the data "
            "couldn't be fetched correctly from the beacon client\n" + fg.rs
        )
        return 0


def test_standard_logging_for_supplied_pubkey() -> int:
    """Test whether pubkeys are fetched correctly from the chain

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        f"Validator {CONFIG.validators.full_identifier.index} has next ATTESTATION"
    ]
    command = get_general_eth_duties_start_command(
        [CONFIG.validators.full_identifier.pubkey],
        CONFIG.general.working_beacon_node_url,
    )
    return run_generic_test(
        expected_logs,
        command,
        "standard logging for supplied pubkey",
        "duties will be executed",
        additional_failure_message=(
            "It is possible that the data couldn't be fetched correctly from the beacon client"
        ),
    )


def test_pubkey_logging_mode() -> int:
    """Test whether pubkeys are logged correctly instead of indices

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [CONFIG.validators.full_identifier.pubkey]
    command = get_general_eth_duties_start_command(
        [CONFIG.validators.full_identifier.index],
        CONFIG.general.working_beacon_node_url,
    ) + ["--log-pubkeys"]
    return run_generic_test(
        expected_logs,
        command,
        "pubkey logging mode",
        "duties will be executed",
        drop_expected_logs=True,
    )


def test_alias_logging_mode() -> int:
    """Test whether aliases are set correctly

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["my_index", "my_pubkey"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.with_alias, CONFIG.general.working_beacon_node_url
    )
    return run_generic_test(
        expected_logs,
        command,
        "alias logging mode",
        "duties will be executed",
        drop_expected_logs=True,
    )


def test_set_logging_colors() -> int:
    """Test whether colors for warning and critical logs are set correctly

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = ["153;255;204", "255;51;153"]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general, CONFIG.general.working_beacon_node_url
    ) + [
        "--log-color-warning",
        "153,255,204",
        "--log-color-critical",
        "255,51,153",
        "--log-time-warning",
        "480",
        "--log-time-critical",
        "240",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "set logging colors",
        "duties will be executed",
        drop_expected_logs=True,
        additional_failure_message=(
            "This is most likely due to the fact that not a single validator "
            "was in the range for the colorful warning or critical logging."
        ),
    )


def test_set_colorful_logging_thresholds_execution() -> int:
    """Test whether colorful logging thresholds are set properly


    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    validators_to_test = CONFIG.validators.active.not_in_sync_committee_not_proposing
    command = command = get_general_eth_duties_start_command(
        validators_to_test, CONFIG.general.working_beacon_node_url
    ) + [
        "--log-time-warning",
        "480",
        "--log-time-critical",
        "240",
    ]
    try:
        test_set_colorful_logging_thresholds(command, "duties will be executed")
        return 1
    except AssertionError:
        print(fg.red + "Test Failed\n" + fg.rs)
        return 0


def test_logging_duties_for_high_number_of_validators() -> int:
    """Test correct high number of validators

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Provided number of validators for fetching attestation duties is high"
    ]
    command = [
        "poetry",
        "run",
        "python",
        ETH_DUTIES_ENTRY_POINT,
        "--validators-file",
        str(Path.cwd() / "test/data/devnet-validators"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
    ]
    return run_generic_test(
        expected_logs,
        command,
        "logging duties for high number of validators",
        expected_logs[0],
    )


def test_omit_attestation_duties() -> int:
    """Test omit attestation duties

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: log",
        "No upcoming duties detected!",
    ]
    command = get_general_eth_duties_start_command(
        [CONFIG.validators.active.not_in_sync_committee_not_proposing[0]],
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--omit-attestation-duties",
        "--omit-sync-committee-duties",
        "--omit-ptc-duties",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "omit attestation duties",
        "Logging next duties interval",
        overhead_log_number=10,
        additional_failure_message=(
            "It could be that the provided validator is inactive, "
            "in sync committee or about to propose a block!"
        ),
        drop_expected_logs=True,
    )


def test_omit_sync_committee_duties() -> int:
    """Test omit sync committee duties

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: log",
        "Logging sync_committee duties is omitted by the user",
        "No upcoming duties detected!",
    ]
    command = get_general_eth_duties_start_command(
        [CONFIG.validators.active.in_sync_committee[0]],
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--omit-sync-committee-duties",
        "--omit-attestation-duties",
        "--omit-ptc-duties",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "omit sync committee duties",
        "Logging next duties interval",
        overhead_log_number=10,
        additional_failure_message=(
            "It could be that the provided validator is inactive "
            "or about to propose a block!"
        ),
        drop_expected_logs=True,
    )


def test_omit_ptc_duties() -> int:
    """Test omit ptc duties

    Skips if no validator of the configured pool currently holds a ptc duty,
    which is the case on any pre-Gloas devnet.

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    validators_with_ptc_duty = get_validators_with_ptc_duty(
        CONFIG.validators.active.general
    )
    if not validators_with_ptc_duty:
        return skip_test(
            "omit ptc duties",
            "No validator of the configured pool has an upcoming ptc duty. "
            "This is expected on a pre-Gloas devnet.",
        )
    expected_logs = [
        "Started in mode: log",
        "Logging ptc duties is omitted by the user",
        "No upcoming duties detected!",
    ]
    command = get_general_eth_duties_start_command(
        [validators_with_ptc_duty[0]],
        CONFIG.general.working_beacon_node_url,
    ) + [
        "--omit-ptc-duties",
        "--omit-attestation-duties",
        "--omit-sync-committee-duties",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "omit ptc duties",
        "Logging next duties interval",
        overhead_log_number=10,
        additional_failure_message=(
            "It could be that the provided validator is inactive "
            "or about to propose a block!"
        ),
        drop_expected_logs=True,
    )


def test_ptc_duty_logging() -> int:
    """Test that an upcoming ptc duty is logged in the standard slot based format

    Skips if no validator of the configured pool currently holds a ptc duty,
    which is the case on any pre-Gloas devnet.

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    validators_with_ptc_duty = get_validators_with_ptc_duty(
        CONFIG.validators.active.general
    )
    if not validators_with_ptc_duty:
        return skip_test(
            "ptc duty logging",
            "No validator of the configured pool has an upcoming ptc duty. "
            "This is expected on a pre-Gloas devnet.",
        )
    expected_logs = ["next PTC duty"]
    command = get_general_eth_duties_start_command(
        [validators_with_ptc_duty[0]],
        CONFIG.general.working_beacon_node_url,
    ) + ["--omit-attestation-duties", "--omit-sync-committee-duties"]
    return run_generic_test(
        expected_logs,
        command,
        "ptc duty logging",
        "Logging next duties interval",
        overhead_log_number=10,
        drop_expected_logs=True,
    )


def test_increase_of_max_slot_based_duty_logs() -> int:
    """Test increase of max slot based duty logs

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "Started in mode: log",
        "Logging next duties interval...",
    ]
    command = [
        "poetry",
        "run",
        "python",
        ETH_DUTIES_ENTRY_POINT,
        "--validators-file",
        str(Path.cwd() / "test/data/devnet-validators-small"),
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
        "--max-slot-based-duty-logs",
        "61",
    ]
    return run_generic_test(
        expected_logs,
        command,
        "increase of max slot based duty logs",
        "all duties will be executed",
    )


def test_logged_format_of_time_to_next_sync_committee() -> int:
    """Test logging format of time to next sync committee

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.in_sync_committee,
        CONFIG.general.working_beacon_node_url,
    )
    try:
        test_time_to_next_sync_committee_format(command, "duties will be executed")
        return 1
    except AssertionError:
        print(fg.red + "Test Failed" + fg.rs)
        return 0


def test_standard_logging_mode_when_identifiers_fetched_from_validator_nodes() -> int:
    """Test for active and inactive validators supplied via --validator-nodes

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [
        "next ATTESTATION duty",
        "next PROPOSING duty",
        "is in current sync committee",
    ]
    validators_to_test = CONFIG.validator_nodes.single_node_indices
    command = get_eth_duties_entry_point() + [
        "--beacon-nodes",
        CONFIG.general.working_beacon_node_url,
        "--validator-nodes",
        str(Path.cwd() / "test/data/online-single-validator-node"),
    ]
    try:
        test_standard_logging_mode(
            command, "duties will be executed", expected_logs, validators_to_test
        )
        return 1
    except AssertionError:
        print(fg.red + "Test Failed" + fg.rs)
        print(
            fg.red + "It is possible that the data "
            "couldn't be fetched correctly from the beacon client\n" + fg.rs
        )
        return 0
