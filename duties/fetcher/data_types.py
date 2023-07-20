"""Defines different data types
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from dataclass_wizard import JSONWizard


class DutyType(Enum):
    """Defines a validator duty type"""

    NONE = "none"
    ATTESTATION = "attestation"
    SYNC_COMMITTEE = "sync_committee"
    PROPOSING = "proposing"


@dataclass
class ValidatorDuty(JSONWizard):
    """Validator duty relevant data points"""

    pubkey: str
    validator_index: str
    epoch: int = 0
    slot: int = 0
    validator_sync_committee_indices: List[int] = field(default_factory=list)
    type: DutyType = DutyType.NONE
    time_to_duty: int = 0


@dataclass
class ValidatorData:
    """Representation of validator data as returned by /eth/v1/beacon/states/<state>/validators"""

    pubkey: str


@dataclass
class ValidatorIdentifier(JSONWizard):
    """Representation of validator metadata as returned by
    /eth/v1/beacon/states/<state>/validators
    """

    index: str = ""
    validator: ValidatorData = ValidatorData("")
    alias: str | None = None
