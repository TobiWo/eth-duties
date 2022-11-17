"""Defines different data types
"""

from dataclasses import dataclass
from enum import Enum
from dataclass_wizard import JSONWizard


class DutyType(Enum):
    """
    Defines a validator duty type
    """

    ATTESTATION = 1
    PROPOSING = 2


@dataclass
class ValidatorDuty(JSONWizard):
    """
    Validator duty relevant data points
    """

    pubkey: str
    validator_index: int
    slot: int
    type: DutyType = DutyType.ATTESTATION
