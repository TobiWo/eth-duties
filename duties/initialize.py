"""Module which initializes necessary program components
"""
# pylint: disable=import-error

from argparse import Namespace
from os import path
from logging import config as logging_config
from yaml import safe_load
from cli.cli import get_arguments
from colorama import init

__logging_configuration_path = path.abspath(
    path.join(path.dirname(__file__), "..", "config", "logging_config.yaml")
)


def initialize() -> None:
    """Initializes logger and colorama"""
    arguments = get_arguments()
    __initialize_logging(arguments)
    __initialize_colorama()


def __initialize_logging(arguments: Namespace) -> None:
    """_summary_
    Helper function to load logging configuration and setup the logger
    """
    with open(file=__logging_configuration_path, mode="r", encoding="utf-8") as f:
        config = safe_load(f.read())
        config["handlers"]["console"]["level"] = arguments.log.upper()
        logging_config.dictConfig(config)


def __initialize_colorama() -> None:
    init()
