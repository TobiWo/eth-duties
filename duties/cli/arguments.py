"""
Module for parsing CLI arguments
"""

from argparse import ArgumentError, ArgumentParser, FileType, Namespace
from typing import List


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
        help=(
            "The max. number of validators for which attestation duties will be logged "
            "(default: 50)"
        ),
        action="store",
        default=50,
    )
    parser.add_argument(
        "--omit-attestation-duties",
        help="If supplied upcoming attestation duties will not be logged to the console",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--validators",
        type=str,
        help="One or many validator identifiers for which next duties will be fetched",
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
    if (validators and validators_file) or (not validators and not validators_file):
        raise ArgumentError(
            None,
            "ONE of the following flags is required: '--validators|-v', '--validator-file|-f'",
        )


def __validate_log_times(
    passed_log_time_warning: float, passed_log_time_critical: float
) -> None:
    if passed_log_time_warning <= 0 or passed_log_time_critical <= 0:
        raise ValueError("Passed time values should be > 0")
    if passed_log_time_warning < passed_log_time_critical:
        raise ArgumentError(
            None,
            f"Passed seconds for '--log-time-warning' (supplied or default: "
            f"{passed_log_time_warning}) needs to be greater "
            f"than for '--log-time-critical' (supplied or default: {passed_log_time_critical})",
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
    return arguments


ARGUMENTS = __set_arguments()
