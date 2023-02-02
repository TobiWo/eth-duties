"""Initializes necessary program components
"""

import sys
from argparse import Namespace
from logging import config as logging_config
from os import path

from cli.arguments import ARGUMENTS
from colorama import init
from yaml import safe_load


def __initialize() -> None:
    """Initializes logger and colorama"""
    __initialize_logging(ARGUMENTS)
    __initialize_colorama()


def __initialize_logging(arguments: Namespace) -> None:
    """Helper function to load and set logging configuration"""
    with open(
        file=__get_logging_configuration_path(), mode="r", encoding="utf-8"
    ) as configuration_file:
        config = safe_load(configuration_file.read())
        config["handlers"]["console"]["level"] = arguments.log.upper()
        logging_config.dictConfig(config)


def __get_logging_configuration_path() -> str:
    logging_configuration_path = getattr(
        sys,
        "_MEIPASS",
        path.abspath(
            path.join(
                path.dirname(__file__), "..", "..", "config", "logging_config.yaml"
            )
        ),
    )
    if "_MEI" in logging_configuration_path:
        logging_configuration_path = path.abspath(
            path.join(logging_configuration_path, "config", "logging_config.yaml")
        )
    return logging_configuration_path


def __initialize_colorama() -> None:
    """Initializes coloroma so that colorful logging works independent from OS"""
    init()


__initialize()
