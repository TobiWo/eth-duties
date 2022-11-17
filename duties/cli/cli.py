"""
Module for parsing CLI arguments
"""

from argparse import ArgumentParser, Namespace, FileType


def __get_raw_arguments() -> Namespace:
    parser = ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "-b",
        "--beacon-node",
        type=str,
        help="URL to access the beacon node api (default: http://localhost:5052)",
        action="store",
        default="http://localhost:5052",
    )
    group.add_argument(
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
    group.add_argument(
        "-v",
        "--validators",
        type=str,
        help="One or many validator indices for which next duties will be fetched",
        action="store",
        nargs="+",
    )
    return parser.parse_args()


def __validate_fetching_interval(passed_fetching_interval: int) -> None:
    if passed_fetching_interval < 12:
        raise ValueError(
            "The interval should be greater or equal the slot time (12 seconds)"
        )


def get_arguments() -> Namespace:
    """
    Parses cli arguments passed by the user

    Returns:
        Namespace: Parsed arguments
    """
    arguments = __get_raw_arguments()
    __validate_fetching_interval(arguments.interval)
    return arguments
