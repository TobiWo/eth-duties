"""Defines different data types
"""

from dataclasses import dataclass, field
from enum import Enum
from dataclass_wizard import JSONWizard
from typing import List


class DutyType(Enum):
    """Defines a validator duty type"""

    NONE = 0
    ATTESTATION = 1
    SYNC_COMMITTEE = 2
    PROPOSING = 3


@dataclass
class ValidatorDuty(JSONWizard):
    """Validator duty relevant data points"""

    pubkey: str
    validator_index: int
    epoch: int = 0
    slot: int = 0
    validator_sync_committee_indices: List[int] = field(default_factory=list)
    type: DutyType = DutyType.NONE
