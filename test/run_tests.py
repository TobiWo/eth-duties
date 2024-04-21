"""Module to run test suite
"""

# pylint: disable=line-too-long

from cases import (
    test_cicd_mode,
    test_cli_validation,
    test_logging_mode,
    test_rest_api,
    test_startup,
)
from sty import fg  # type: ignore[import]
from tqdm import tqdm

print(
    (
        "TIME CONSUMPTION OF THE TEST SUIT DEPENDS ON THE STABILITY OF YOUR BEACON NODE "
        "CONNECTION AND MAY TAKE LONGER IF YOUR NODE IS UNDER HEAVY LOAD ALREADY!"
    )
)

test_cases = [
    # Test startup
    test_startup.test_no_beacon_connection_at_startup,
    # Test rest api
    test_rest_api.test_get_block_proposing_duties_from_rest_endpoint,
    test_rest_api.test_get_sync_committee_duties_from_rest_endpoint,  # test will currently fail on kurtosis devnet (see here: https://github.com/TobiWo/eth-duties/issues/78)
    test_rest_api.test_get_attestation_duties_from_rest_endpoint,
    test_rest_api.test_rest_while_running_in_cicd_mode,
    test_rest_api.test_post_new_validator_identifier_rest_endpoint,
    test_rest_api.test_delete_validator_identifier_rest_endpoint,
    test_rest_api.test_start_rest_api_on_different_port,
    test_rest_api.test_start_rest_api_on_port_in_usage,
    # Test logging mode
    test_logging_mode.test_standard_logging_mode_execution,
    test_logging_mode.test_set_colorful_logging_thresholds_execution,
    test_logging_mode.test_standard_logging_for_supplied_pubkey,
    test_logging_mode.test_pubkey_logging_mode,
    test_logging_mode.test_alias_logging_mode,
    test_logging_mode.test_set_logging_colors,
    test_logging_mode.test_logging_duties_for_high_number_of_validators,
    test_logging_mode.test_omit_attestation_duties,
    test_logging_mode.test_increase_of_max_attestation_duty_logs,
    test_logging_mode.test_logged_format_of_time_to_next_sync_committee,
    # Test cli validation
    test_cli_validation.test_any_validators_flag_validation,
    test_cli_validation.test_both_validators_flag_validation,
    test_cli_validation.test_interval_flag_validation,
    test_cli_validation.test_log_time_warning_flag_validation,
    test_cli_validation.test_cicd_attestation_proportion_flag_validation,
    test_cli_validation.test_cicd_waiting_time_flag_validation,
    # Test cicd mode
    test_cicd_mode.test_cicd_exit_mode_with_sync_committee_duties_while_proportion_of_attestation_duties_is_above_threshold,
    test_cicd_mode.test_cicd_exit_mode_without_sync_committee_duties_while_proportion_of_attestation_duties_is_above_threshold,
    test_cicd_mode.test_cicd_exit_mode_with_sync_committee_duties_while_proportion_of_duties_is_not_above_threshold,
    test_cicd_mode.test_cicd_exit_mode_without_sync_committee_duties_while_proportion_of_duties_is_not_above_threshold,
    test_cicd_mode.test_cicd_force_graceful_exit_mode,
    test_cicd_mode.test_cicd_wait_mode_without_sync_committee_duties_while_proportion_of_duties_is_above_threshold_within_waiting_time,
    test_cicd_mode.test_cicd_wait_mode_while_waiting_time_exceeds,
]

SUCCESSFUL_TEST_COUNTER = 0
for test_function in tqdm(test_cases, desc="Running...", ascii=False, ncols=75):
    SUCCESSFUL_TEST_COUNTER += test_function()

TOTAL_TEST_COUNTER = len(test_cases)
if SUCCESSFUL_TEST_COUNTER != TOTAL_TEST_COUNTER:
    print(fg.red + "\nONE OR MULTIPLE TESTS FAILED!" + fg.rs)
    print(
        (
            fg.red
            + "IF YOU RUN THESE TESTS MULTIPLE TIMES AND THEY FAIL ALL THE TIME, "
            "PLEASE OPEN AN ISSUE ON GITHUB WITH SOME DETAILS (WHICH TEST FAILED ETC.). "
            "THANK YOU!!!" + fg.rs
        )
    )
else:
    print(fg.green + "\nALL TESTS SUCCEDED" + fg.rs)
