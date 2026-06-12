"""Module for rest specific types
"""

from enum import Enum
from typing import List

# pylint: disable-next=no-name-in-module
from pydantic import BaseModel, ConfigDict, Field


class HttpMethod(Enum):
    """Enum for http methods"""

    POST = "POST"
    DELETE = "DELETE"


class ValidatorDuties(BaseModel):
    """DTO for rest path /duties/any which indicates
    whether or not there are any upcoming validator duties"""

    any: bool

    model_config = ConfigDict(json_schema_extra={"example": {"any": True}})


class BadValidatorIdentifiers(BaseModel):
    """DTO for rest path /validator/identifier which highlights
    provided validators which are provided in a bad format"""

    identifiers: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={"example": {"identifiers": ["not-a-pubkey", "0xtoo-short"]}}
    )


class NoBeaconNodeConnection(BaseModel):
    """DTO for rest path /duties/raw which indicates that non
    of the provided beacon nodes is available"""

    message: str = "No healthy beacon node connection available"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "No healthy beacon node connection available"}
        }
    )
