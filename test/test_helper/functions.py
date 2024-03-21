"""Module containig test function implementations
"""

from re import findall
from typing import Callable, List

from sty import fg  # type: ignore[import]
from test_helper.chain import (
    get_number_of_active_validators,
    get_number_of_validators_in_current_sync_comittee,
    get_number_of_validators_which_will_propose_block,
)
from test_helper.general import compare_logs, print_test_message, run_eth_duties


def test_standard_logging_mode(
    command: List[str],
    process_termination_log: str,
    expected_logs: List[str],
    validators_to_test: List[str],
) -> None:
    """Test eth-duties standard logging behavior

    Args:
        command (List[str]): eth-duties start command
        process_termination_log (str): Log which is used to terminate the subprocess
        expected_logs (List[str]): Expected logs while eth-duties subprocess is running
        validators_to_test (List[str]): Tested validators
    """
    print_test_message(test_standard_logging_mode)
    number_of_active_validators = get_number_of_active_validators(validators_to_test)
    number_of_validators_in_current_sync_comittee = (
        get_number_of_validators_in_current_sync_comittee(validators_to_test)
    )
    number_of_validators_which_will_propose_block = (
        get_number_of_validators_which_will_propose_block(validators_to_test)
    )
    expected_log_counter = (
        number_of_active_validators + number_of_validators_in_current_sync_comittee
    ) + number_of_validators_which_will_propose_block
    logs = run_eth_duties(command, process_termination_log, None, None)
    number_of_matched_logs = compare_logs(logs[0], expected_logs, False)
    assert number_of_matched_logs == expected_log_counter
    print(fg.green + "\rTest succeeded" + fg.rs)


# # Specific test function 2
def test_set_colorful_logging_thresholds(
    command: List[str],
    process_termination_log: str,
    expected_logs: List[str] | None = None,
    validators_to_test: List[str] | None = None,
) -> None:
    """Test whether colors are logged correctly using default logging colors

    Args:
        command (List[str]): eth-duties start command
        process_termination_log (str): Log which is used to terminate the subprocess
        expected_logs (List[str] | None, optional): Expected logs while eth-duties subprocess
        is running. Defaults to None.
        validators_to_test (List[str] | None, optional): Tested validators. Defaults to None.
    """
    print_test_message(test_set_colorful_logging_thresholds)
    logs = run_eth_duties(command, process_termination_log, None, None)
    critical_counter = 0
    critical_match_counter = 0
    warning_counter = 0
    warning_match_counter = 0
    for log in logs[0]:
        if "255;0;0" in log:
            critical_counter += 1
            critical_match = findall("([0-3]{2}:[0-9]{2}\\smin)|(04:00 min)", log)
            if len(critical_match) > 0:
                critical_match_counter += 1
        if "255;255;0" in log:
            warning_counter += 1
            warning_match = findall("[0-1][4-9]:(?!00)[0-9]{2}\\smin", log)
            if len(warning_match) > 0:
                warning_match_counter += 1
    assert critical_counter == critical_match_counter
    assert warning_counter == warning_match_counter
    print(fg.green + "\rTest succeeded" + fg.rs)


def generic_test(
    expected_logs: List[str],
    command: List[str],
    test_message: str,
    process_termination_log: str,
    parse_stderr: bool,
    drop_expected_logs: bool,
    rest_call: Callable[[], None] | None,
    rest_call_trigger_log: str | None,
    test_rest_response_length: bool,
    overhead_log_number: int,
) -> None:
    """Generic test function which is used for most tests

    Args:
        expected_logs (List[str]): Expected logs while eth-duties subprocess is running
        command (List[str]): eth-duties start command
        test_message (str): Message printed to the console
        process_termination_log (str): Log which is used to terminate the subprocess
        parse_stderr (bool, optional): Parse stderr or stdout from subprocess. Defaults to False.
        drop_expected_logs (bool, optional): Whether logs will be dropped from provided expected
        logs list during search process. Defaults to False.
        rest_call (Callable[[], None] | None, optional): Function which sends a rest call.
        Defaults to None.
        rest_call_trigger_log (str | None, optional): Log which will trigger the rest call.
        Defaults to None.
        test_rest_response_length (bool, optional): Whether or not to test the response object
        from the rest call for it's length. Defaults to True.
        overhead_log_number (int, optional): Logs which will be collected after process
        termination log was found. Defaults to 1.
    """
    print_test_message(test_message=test_message)
    number_of_expected_logs = len(expected_logs)
    process_output = run_eth_duties(
        command,
        process_termination_log,
        rest_call,
        rest_call_trigger_log,
        parse_stderr,
        overhead_log_number,
    )
    number_of_matched_logs = compare_logs(
        process_output[0], expected_logs, drop_expected_logs
    )
    if rest_call and rest_call_trigger_log:
        assert process_output[1].status_code in (200, 201)
        if test_rest_response_length:
            assert len(list(process_output[1].json())) == number_of_expected_logs
    assert number_of_matched_logs == number_of_expected_logs


def run_generic_test(
    expected_logs: List[str],
    command: List[str],
    test_message: str,
    process_termination_log: str,
    parse_stderr: bool = False,
    drop_expected_logs: bool = False,
    rest_call: Callable[[], None] | None = None,
    rest_call_trigger_log: str | None = None,
    test_rest_response_length: bool = True,
    overhead_log_number: int = 1,
    additional_failure_message: str = "",
) -> int:
    """Wrapper to run a generic test

    Args:
        expected_logs (List[str]): Expected logs while eth-duties subprocess is running
        command (List[str]): eth-duties start command
        test_message (str): Message printed to the console
        process_termination_log (str): Log which is used to terminate the subprocess
        parse_stderr (bool, optional): Parse stderr or stdout from subprocess. Defaults to False.
        drop_expected_logs (bool, optional): Whether logs will be dropped from provided expected
        logs list during search process. Defaults to False.
        rest_call (Callable[[], None] | None, optional): Function which sends a rest call.
        Defaults to None.
        rest_call_trigger_log (str | None, optional): Log which will trigger the rest call.
        Defaults to None.
        test_rest_response_length (bool, optional): Whether or not to test the response object
        from the rest call for it's length. Defaults to True.
        overhead_log_number (int, optional): Logs which will be collected after process
        termination log was found. Defaults to 1.
        additional_failure_message (str, optional): Additional failure message. Defaults to ""

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    try:
        generic_test(
            expected_logs,
            command,
            test_message,
            process_termination_log,
            parse_stderr,
            drop_expected_logs,
            rest_call,
            rest_call_trigger_log,
            test_rest_response_length,
            overhead_log_number,
        )
        print(fg.green + "Test succeeded\n" + fg.rs)
        return 1
    except AssertionError:
        if not additional_failure_message:
            print(fg.red + "Test Failed\n" + fg.rs)
        if additional_failure_message:
            print(fg.red + "Test Failed" + fg.rs)
            print(fg.red + additional_failure_message + fg.rs)
        return 0
