"""
Module for parsing CLI arguments
"""

from argparse import ArgumentError, ArgumentParser, FileType, Namespace
from itertools import chain
from typing import List

from cli.parse import parse_validator_identifiers
from cli.types import Mode


def __get_raw_arguments() -> Namespace:
    """Parses cli arguments passed by the user

    Returns:
        Namespace: Parsed cli arguments
    """
    parser = ArgumentParser(
        prog="eth-duties",
        description="Tool for logging validator duties",
        usage="eth-duties [...options]",
    )
    parser.add_argument(
        "--beacon-node",
        type=str,
        help="URL to access the beacon node api (default: http://localhost:5052)",
        action="store",
        default="http://localhost:5052",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Interval in seconds for fetching data from the beacon node (default: 15)",
        action="store",
        default=15,
    )
    parser.add_argument(
        "--log",
        type=str,
        help="Defines log level. Values are 'DEBUG' or 'INFO' (default: 'INFO')",
        action="store",
        default="INFO",
    )
    parser.add_argument(
        "--log-pubkeys",
        help="If supplied the validator index will be replaced with the pubkey in log messages",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--log-time-warning",
        type=float,
        help="The threshold at which a time to duty warning log (in seconds) "
        "gets colored in YELLOW (default: 120)",
        action="store",
        default=120.0,
    )
    parser.add_argument(
        "--log-time-critical",
        type=float,
        help="The threshold at which a time to duty critical log (in seconds) "
        "gets colored in RED (default: 60)",
        action="store",
        default=60.0,
    )
    parser.add_argument(
        "--max-attestation-duty-logs",
        type=int,
        help=(
            "The max. number of validators for which attestation duties will be logged "
            "(default: 50)"
        ),
        action="store",
        default=50,
    )
    parser.add_argument(
        "--mode",
        help=(
            "The mode which eth-duties will run with. "
            "Values are 'log', 'cicd-exit', 'cicd-wait' or 'cicd-force-graceful-exit' (default: 'log')"
        ),
        type=Mode,
        choices=Mode,
        default=Mode.LOG,
    )
    parser.add_argument(
        "--mode-cicd-waiting-time",
        type=int,
        help=(
            "The max. waiting time until eth-duties exits in cicd-wait mode "
            "(default 780 sec. (approx. 2 epochs))"
        ),
        action="store",
        default=780,
    )
    parser.add_argument(
        "--mode-cicd-attestation-time",
        type=int,
        help=(
            "If a defined proportion of attestion duties is above the defined time threshold "
            "the application exits gracefully in any cicd-mode "
            "(default 240 sec.)"
        ),
        action="store",
        default=240,
    )
    parser.add_argument(
        "--mode-cicd-attestation-proportion",
        type=float,
        help=(
            "The proportion of attestation duties which needs to be above a defined "
            "time threshold to force the application to exit gracefully "
            "(default 1)"
        ),
        action="store",
        default=1,
    )
    parser.add_argument(
        "--omit-attestation-duties",
        help="If supplied upcoming attestation duties will not be logged to the console",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--validators",
        type=parse_validator_identifiers,
        help=(
            "One or many validator identifiers for which next duties will be fetched. "
            "Validator identifiers need to be separated by space or comma. "
            "Argument can be provided multiple times."
        ),
        action="append",
        nargs="*",
    )
    parser.add_argument(
        "--validators-file",
        type=FileType("r"),
        help="File with validator identifiers where every identifier is on a separate line",
        action="store",
    )
    return parser.parse_args()


def __validate_fetching_interval(passed_fetching_interval: int) -> None:
    """Validates whether the fetching interval is set above a lower threshold of 12 seconds

    Args:
        passed_fetching_interval (int): Passed interval in seconds

    Raises:
        ValueError: Error for wrongly provided interval user input
    """
    if passed_fetching_interval < 12:
        raise ValueError(
            "The interval should be greater or equal the slot time (12 seconds)"
        )


def __validate_provided_validator_flag(
    validators: List[str] | None, validators_file: str | None
) -> None:
    """Validates that only one of the validator flags was provided

    Args:
        validators (List[str] | None): Provided validators
        validators_file (str | None): Provided validators as file

    Raises:
        ArgumentError: Error that only one of the provided flags is allowed
    """
    if (validators and validators_file) or (not validators and not validators_file):
        raise ArgumentError(
            None,
            "ONE of the following flags is required: '--validators', '--validators-file'",
        )


def __validate_log_times(
    passed_log_time_warning: float, passed_log_time_critical: float
) -> None:
    """Validates the provided log time values

    Args:
        passed_log_time_warning (float): Provided log time warning value
        passed_log_time_critical (float): Provided log time critical value

    Raises:
        ValueError: Error if any of the provided values is <= 0
        ArgumentError: Error if warning value is smaller than critical value
    """
    if passed_log_time_warning <= 0 or passed_log_time_critical <= 0:
        raise ValueError("Passed time values should be > 0")
    if passed_log_time_warning < passed_log_time_critical:
        raise ArgumentError(
            None,
            f"Passed seconds for '--log-time-warning' (supplied or default: "
            f"{passed_log_time_warning}) needs to be greater "
            f"than for '--log-time-critical' (supplied or default: {passed_log_time_critical})",
        )


def __validate_cicd_waiting_time(
    passed_fetching_interval: int, passed_cicd_waiting_time: int, passed_mode: Mode
) -> None:
    """Validates whether provided cicd waiting time is greater then provided fetching interval
    in cicd-wait mode

    Args:
        passed_fetching_interval (int): Provided fetching interval
        passed_cicd_waiting_time (int): Provided cicd waiting time
        passed_mode (Mode): Provided mode

    Raises:
        ValueError: Error if cicd waiting time is smaller than fetching interval
    """
    if (
        passed_cicd_waiting_time < passed_fetching_interval
    ) and passed_mode == Mode.CICD_WAIT:
        raise ValueError(
            "The value for flag '--mode-cicd-waiting-time' should be >= "
            "the passed fetching interval (defined with '--interval')"
        )


def __validate_cicd_attestation_proportion(
    passed_cicd_attestation_proportion: float, passed_mode: Mode
) -> None:
    """Validates whether provided cicd attestation proportion is between 0 and 1 while running
    in any cicd mode

    Args:
        passed_cicd_attestation_proportion (float): Provided cicd attestation proportion

    Raises:
        ValueError: Error if cicd attestation proportion value is not between 0 and 1
    """
    if (
        passed_cicd_attestation_proportion > 1
        or passed_cicd_attestation_proportion < 0
        and (passed_mode != Mode.LOG)
    ):
        raise ValueError(
            "The value for flag '--mode-cicd-attestation-proportion' should be between 0 and 1"
        )


def __set_arguments() -> Namespace:
    """Parses cli arguments passed by the user

    Returns:
        Namespace: Parsed arguments
    """
    arguments = __get_raw_arguments()
    __validate_fetching_interval(arguments.interval)
    __validate_provided_validator_flag(arguments.validators, arguments.validators_file)
    __validate_log_times(arguments.log_time_warning, arguments.log_time_critical)
    __validate_cicd_waiting_time(
        arguments.interval, arguments.mode_cicd_waiting_time, arguments.mode
    )
    __validate_cicd_attestation_proportion(
        arguments.mode_cicd_attestation_proportion, arguments.mode
    )
    if arguments.validators:
        arguments.validators = list(chain(*list(arguments.validators)))
    return arguments


ARGUMENTS = __set_arguments()
