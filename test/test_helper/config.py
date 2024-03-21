"""Config related module
"""

from dataclasses import dataclass
from pathlib import Path
from sys import path
from typing import List

from dataclass_binder import Binder

path.append(str(Path.cwd() / "duties"))


@dataclass
class General:
    """General config section"""

    failing_beacon_node_url: str
    working_beacon_node_url: str
    rest_port: str
    rest_port_in_usage: str


@dataclass
class ActiveValidators:
    """Active validator config section"""

    general: List[str]
    in_sync_committee: List[str]
    next_sync_committee: List[str]
    proposing_blocks: List[str]
    with_alias: List[str]


@dataclass
class ValidatorWithFullIdentifier:
    """Validator with both identifiers config section"""

    index: str
    pubkey: str


@dataclass
class Validators:
    """Validators config section"""

    inactive: List[str]
    active: ActiveValidators
    full_identifier: ValidatorWithFullIdentifier


@dataclass
class Config:
    """Config class"""

    general: General
    validators: Validators


CONFIG = Binder(Config).parse_toml(Path.cwd() / "test/config.toml")
ETH_DUTIES_ENTRY_POINT = str(Path.cwd() / "duties/main.py")


def validate_config() -> None:
    """Validate provided config

    Raises:
        ValueError: Error when any config option is missing
    """
    error_counter = 0
    for field in CONFIG.general.__dataclass_fields__:
        value = getattr(CONFIG.general, field)
        if not value:
            print("Missing general property in test_config.toml")
            error_counter += 1
    if not CONFIG.validators.inactive:
        print("Missing inactive validator identifiers")
        error_counter += 1
    for field in CONFIG.validators.active.__dataclass_fields__:
        value = getattr(CONFIG.validators.active, field)
        if not value:
            print("Missing some active validator identifiers")
            error_counter += 1
    for field in CONFIG.validators.full_identifier.__dataclass_fields__:
        value = getattr(CONFIG.validators.full_identifier, field)
        if not value:
            print("Missing index or pubkey for validator with both identifiers")
            error_counter += 1
    if error_counter > 0:
        raise ValueError("Missing values in test_config.toml")


validate_config()
