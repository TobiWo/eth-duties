"""
Defines different dataclasses
"""

from dataclasses import dataclass
from enum import Enum
from dataclass_wizard import JSONWizard


@dataclass
class RawValidatorDuty(JSONWizard):
    pubkey: str
    validator_index: int
    slot: int


class DutyType(Enum):
    ATTESTATION = 1
    PROPOSING = 2


@dataclass
class ValidatorDuty:
    validator_index: int
    target_slot: int
    type: DutyType
