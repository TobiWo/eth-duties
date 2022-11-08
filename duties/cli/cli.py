"""
Module for parsing CLI arguments
"""

from argparse import ArgumentParser, Namespace, FileType


def get_arguments() -> Namespace:
    """
    Parses cli arguments passed by the user

    Returns:
        Namespace: Parsed arguments
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
        "-o",
        "--omit-attestation-duties",
        help="If supplied upcoming attestation duties will not be printed to the console",
        action="store_true",
        default=False,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-v",
        "--validators",
        type=str,
        help="One or many validator indices for which next duties will be fetched",
        action="store",
        nargs="+",
    )
    group.add_argument(
        "-f",
        "--validator-file",
        type=FileType("r"),
        help="File with validator indices where every indice is on a separate line",
        action="store",
    )
    return parser.parse_args()
