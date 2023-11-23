"""Defines different data types
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class DutyType(Enum):
    """Defines a validator duty type"""

    NONE = "none"
    ATTESTATION = "attestation"
    SYNC_COMMITTEE = "sync_committee"
    PROPOSING = "proposing"


class ValidatorDuty(BaseModel):
    """Validator duty relevant data points"""

    pubkey: str
    validator_index: str
    epoch: int = Field(default=0)
    slot: int = Field(default=0)
    validator_sync_committee_indices: List[int] = Field(default_factory=list)
    type: DutyType = Field(default=DutyType.NONE)
    time_to_duty: int = Field(default=0)


@dataclass
class ValidatorData:
    """Representation of validator data as returned by /eth/v1/beacon/states/<state>/validators"""

    pubkey: str


class ValidatorIdentifier(BaseModel):
    """Representation of validator metadata as returned by
    /eth/v1/beacon/states/<state>/validators
    """

    index: str = Field(default="")
    validator: ValidatorData = Field(default=ValidatorData(""))
    alias: str | None = Field(default=None)
