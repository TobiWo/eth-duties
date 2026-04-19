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
    """Base class for validator duty data."""

    pubkey: str
    validator_index: str
    type: DutyType = Field(default=DutyType.NONE)
    seconds_to_duty: int = Field(default=0)


class AttestationDuty(ValidatorDuty):
    """Attestation duty data."""

    slot: int = Field(default=0)


class ProposingDuty(ValidatorDuty):
    """Block proposing duty data."""

    slot: int = Field(default=0)


class SyncCommitteeDuty(ValidatorDuty):
    """Sync committee duty data."""

    epoch: int = Field(default=0)
    validator_sync_committee_indices: List[int] = Field(default_factory=list)
    seconds_left_in_current_sync_committee: int = Field(default=0)


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
