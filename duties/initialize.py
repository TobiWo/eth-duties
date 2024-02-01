"""Initializes necessary program components
"""

import sys
from logging import config as logging_config
from os import path, system
from typing import Any

from sty import RgbBg, Style, bg  # type: ignore[import]
from yaml import safe_load

from duties.cli.arguments import get_arguments
from duties.constants.program import USED_STY_BACKGROUND_COLOR_NAMES

__ARGUMENTS = get_arguments()


def initialize() -> None:
    """Initializes logger and colorama"""
    system("")
    __initialize_logging()
    __set_colors()


def __initialize_logging() -> None:
    """Helper function to load and set logging configuration"""
    logging_config.dictConfig(get_logging_config(__ARGUMENTS.log))


def get_logging_config(log_level: str) -> Any:
    """Helper function to load and set logging configuration"""
    with open(
        file=__get_logging_configuration_path(), mode="r", encoding="utf-8"
    ) as configuration_file:
        config = safe_load(configuration_file.read())
        config["handlers"]["console"]["level"] = log_level.upper()
        return config


def __get_logging_configuration_path() -> str:
    logging_configuration_path = getattr(
        sys,
        "_MEIPASS",
        path.abspath(
            path.join(path.dirname(__file__), "..", "config", "logging_config.yaml")
        ),
    )
    if "_MEI" in logging_configuration_path:
        logging_configuration_path = path.abspath(
            path.join(logging_configuration_path, "config", "logging_config.yaml")
        )
    return logging_configuration_path


def __set_colors() -> None:
    """Overrides used color attributes of sty package"""
    log_color_arguments = [
        argument
        # pylint: disable-next=protected-access
        for argument in __ARGUMENTS._get_kwargs()
        if argument[0].startswith("log_color")
    ]
    for index, color_name in enumerate(USED_STY_BACKGROUND_COLOR_NAMES):
        setattr(
            bg,
            color_name,
            Style(
                RgbBg(
                    log_color_arguments[index][1][0],
                    log_color_arguments[index][1][1],
                    log_color_arguments[index][1][2],
                )
            ),
        )
