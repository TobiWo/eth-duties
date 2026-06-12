"""Defines different data types
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pubkey": "0x93247f2209abcacf57b75a51dafae777f9dd38bc7053d1af526f220a7489a6d3a2753e5f3e8b1cfe39b56f43611df74a",  # pylint: disable=line-too-long
                "validator_index": "123456",
                "type": "attestation",
                "seconds_to_duty": 42,
                "slot": 9876543,
            }
        }
    )


class ProposingDuty(ValidatorDuty):
    """Block proposing duty data."""

    slot: int = Field(default=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pubkey": "0xa1d1ad0714035353258038e964ae9675dc0252ee22cea896825c01458e1807bfad2f9969338798548d9858a571f7425c",  # pylint: disable=line-too-long
                "validator_index": "234567",
                "type": "proposing",
                "seconds_to_duty": 180,
                "slot": 9876600,
            }
        }
    )


class SyncCommitteeDuty(ValidatorDuty):
    """Sync committee duty data."""

    epoch: int = Field(default=0)
    validator_sync_committee_indices: List[int] = Field(default_factory=list)
    seconds_left_in_current_sync_committee: int = Field(default=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pubkey": "0xb2cd2b84fd3b79dd31b3071d97d6ba81bd3cf88eab1c76e47f1b7f8fe3a2e7b4e8b0a1c5e2f3d4a5b6c7d8e9f0a1b2c3",  # pylint: disable=line-too-long
                "validator_index": "345678",
                "type": "sync_committee",
                "seconds_to_duty": 0,
                "epoch": 308625,
                "validator_sync_committee_indices": [42, 128],
                "seconds_left_in_current_sync_committee": 98304,
            }
        }
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "index": "123456",
                "validator": {
                    "pubkey": "0x93247f2209abcacf57b75a51dafae777f9dd38bc7053d1af526f220a7489a6d3a2753e5f3e8b1cfe39b56f43611df74a"  # pylint: disable=line-too-long
                },
                "alias": "validator-alias",
            }
        }
    )
