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


@dataclass
class ActiveValidators:
    """Active validator config section"""

    general: List[str]
    in_sync_committee: List[str]
    next_sync_committee: List[str]
    proposing_blocks: List[str]
    with_alias: List[str]


@dataclass
class ValidatorsWithBothIdentifier:
    """Validator with both identifiers config section"""

    index: str
    pubkey: str


@dataclass
class Validators:
    """Validators config section"""

    inactive: List[str]
    active: ActiveValidators
    both_identifiers: ValidatorsWithBothIdentifier


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
    if (
        not CONFIG.general.failing_beacon_node_url
        or not CONFIG.general.working_beacon_node_url
    ):
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
    for field in CONFIG.validators.both_identifiers.__dataclass_fields__:
        value = getattr(CONFIG.validators.both_identifiers, field)
        if not value:
            print("Missing index or pubkey for validator with both identifiers")
            error_counter += 1
    if error_counter > 0:
        raise ValueError("Missing values in test_config.toml")


validate_config()
