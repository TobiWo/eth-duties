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
    parser = ArgumentParser()
    parser.add_argument(
        "-b",
        "--beacon-node",
        type=str,
        help="URL to access the beacon node api (default: http://localhost:5052)",
        action="store",
        default="http://localhost:5052",
    )
    parser.add_argument(
        "-f",
        "--validator-file",
        type=FileType("r"),
        help="File with validator indices where every index is on a separate line",
        action="store",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        help="Interval in seconds for fetching data from the beacon node (default: 15 seconds)",
        action="store",
        default=15,
    )
    parser.add_argument(
        "-l",
        "--log",
        type=str,
        help="Defines log level. Values are 'DEBUG' or 'INFO'. Default is 'INFO'",
        action="store",
        default="INFO",
    )
    parser.add_argument(
        "-o",
        "--omit-attestation-duties",
        help="If supplied upcoming attestation duties will not be printed to the console",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--validators",
        type=str,
        help="One or many validator indices for which next duties will be fetched",
        action="store",
        nargs="+",
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
    validators: List[str] | None, validator_file: str | None
) -> None:
    if (validators and validator_file) or (not validators and not validator_file):
        raise ArgumentError(
            None,
            "ONE of the following flags is required: '--validators|-v', '--validator-file|-f'",
        )


def get_arguments() -> Namespace:
    """Parses cli arguments passed by the user

    Returns:
        Namespace: Parsed arguments
    """
    arguments = __get_raw_arguments()
    __validate_fetching_interval(arguments.interval)
    __validate_provided_validator_flag(arguments.validators, arguments.validator_file)
    return arguments
