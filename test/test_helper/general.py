"""Module for general helper functions
"""

from signal import SIGINT
from subprocess import PIPE, Popen
from time import time
from typing import IO, Any, Callable, List, Tuple

from requests import Response
from test_helper.config import CONFIG, ETH_DUTIES_ENTRY_POINT


def print_test_message(
    function: Callable[[List[str], str, List[str], List[str]], None] | None = None,
    test_message: str | None = None,
) -> None:
    """Print message to stdout

    Args:
        function (Callable[[List[str], str, List[str], List[str]], None] | None, optional): Test function which is used to determine printed message. Defaults to None. # pylint: disable=line-too-long
        test_message (str | None, optional): Test message. Defaults to None.
    """
    if not test_message and function:
        test_message = " ".join(function.__name__.split("_")[1:])
    print(f"\nTest {test_message}...")


def kill_process(process: Popen[str]) -> None:
    """Kill Popen subprocess

    Args:
        process (Popen[str]): eth-duties subprocess
    """
    process.send_signal(SIGINT)
    process.wait


def run_eth_duties(
    command: List[str],
    process_termination_log: str,
    rest_call: Callable[[], Any] | None,
    rest_call_trigger_log: str | None,
    parse_stderr: bool = False,
    overhead_log_number: int = 1,
) -> Tuple[List[str], Response]:
    """Start eth-duties subprocess

    Args:
        command (List[str]): eth-duties start command
        process_termination_log (str): Log which is used to terminate the subprocess
        rest_call (Callable[[], Any] | None): Function which sends a rest call
        rest_call_trigger_log (str | None): Log which will trigger the rest call
        parse_stderr (bool, optional): Parse stderr or stdout from subprocess. Defaults to False.
        overhead_log_number (int, optional): Logs which will be collected after process termination log was found. Defaults to 1. # pylint: disable=line-too-long

    Returns:
        Tuple[List[str], Response]: Collected logs and rest response
    """
    with Popen(command, text=True, stdout=PIPE, stderr=PIPE) as eth_duties_process:
        eth_duties_logs: List[str] = []
        rest_response: Response = Response()
        if parse_stderr and eth_duties_process.stderr:
            rest_response = get_rest_response(
                eth_duties_logs,
                eth_duties_process.stderr,
                rest_call,
                rest_call_trigger_log,
            )
            fill_log_collection(
                eth_duties_logs,
                eth_duties_process.stderr,
                process_termination_log,
                overhead_log_number,
            )
        if not parse_stderr and eth_duties_process.stdout:
            rest_response = get_rest_response(
                eth_duties_logs,
                eth_duties_process.stdout,
                rest_call,
                rest_call_trigger_log,
            )
            fill_log_collection(
                eth_duties_logs,
                eth_duties_process.stdout,
                process_termination_log,
                overhead_log_number,
            )
        kill_process(eth_duties_process)
        return (eth_duties_logs, rest_response)


def get_rest_response(
    collected_logs: List[str],
    process_logs: IO[str],
    rest_call: Callable[[], Response] | None,
    rest_call_trigger_log: str | None,
) -> Response:
    """Send rest request

    Args:
        collected_logs (List[str]): Empty or partially filled collected eth-duties logs list
        process_logs (IO[str]): Raw subprocess logs
        rest_call (Callable[[], Response] | None): Function which sends a rest call
        rest_call_trigger_log (str | None): Log which will trigger the rest call

    Returns:
        Response: Rest response object
    """
    rest_response: Response = Response()
    if rest_call and rest_call_trigger_log:
        fill_log_collection(collected_logs, process_logs, rest_call_trigger_log)
        rest_response = rest_call()
    return rest_response


def fill_log_collection(
    collected_logs: List[str],
    process_logs: IO[str],
    process_termination_log: str,
    overhead_log_number: int = 1,
) -> None:
    """Fill collected logs list using call by reference scheme

    Args:
        collected_logs (List[str]): Empty or partially filled collected eth-duties logs list
        process_logs (IO[str]): Raw subprocess logs
        process_termination_log (str): Log which is used to terminate the subprocess
        overhead_log_number (int, optional): Logs which will be collected after process termination log was found. Defaults to 1. # pylint: disable=line-too-long
    """
    start = time()
    end = time()
    overhead_counter = 0
    for line in process_logs:
        if CONFIG.test.debug:
            print(line, end="")
        collected_logs.append(line)
        positive_match = [
            log for log in collected_logs if process_termination_log in log
        ]
        if positive_match:
            overhead_counter += 1
        if overhead_counter == overhead_log_number:
            break
        end = time()
        if end - start >= CONFIG.test.timeout:
            print("Test took too long. Will be skipped!")
            break


def compare_logs(
    collected_logs: List[str],
    expected_logs: List[str],
    drop_expected_logs: bool,
) -> int:
    """Compare expected with collected logs

    Args:
        collected_logs (List[str]): Collected eth-duties logs
        expected_logs (List[str]): Expected logs while eth-duties subprocess is running
        drop_expected_logs (bool): Whether logs will be dropped from provided expected logs list during search process # pylint: disable=line-too-long

    Returns:
        int: Number of found matches of expected logs in collected eth-duties logs
    """
    match_counter = 0
    for log in collected_logs:
        for log_index, expected_log in enumerate(expected_logs):
            if expected_log in log:
                match_counter += 1
                if drop_expected_logs:
                    expected_logs.pop(log_index)
        if len(expected_logs) == 0:
            break
    return match_counter


def get_eth_duties_entry_point() -> List[str]:
    """Get eth duties entry point command for subprocess

    Returns:
        List[str]: eth-duties entry point command
    """
    return [
        "poetry",
        "run",
        "python",
        ETH_DUTIES_ENTRY_POINT,
    ]


def get_general_eth_duties_start_command(
    validators_to_test: List[str], beacon_node: str
) -> List[str]:
    """Get mostly used eth-duties start command

    Args:
        validators_to_test (List[str]): Validators which will be forwarded to start command
        beacon_node (str): Beacon node

    Returns:
        List[str]: eth-duties start command
    """
    return get_eth_duties_entry_point() + [
        "--validators",
        " ".join(validators_to_test),
        "--beacon-nodes",
        beacon_node,
    ]
