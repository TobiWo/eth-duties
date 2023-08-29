"""Module for rest specific types
"""

from enum import Enum
from typing import List

# pylint: disable-next=no-name-in-module
from pydantic import BaseModel


class HttpMethod(Enum):
    """Enum for http methods"""

    POST = "POST"
    DELETE = "DELETE"


class ValidatorDuties(BaseModel):
    """DTO for rest path /duties/any which indicates
    whether or not there are any upcoming validator duties"""

    any: bool


class BadValidatorIdentifiers(BaseModel):
    """DTO for rest path /validator/identifier which highlights
    provided validators which are provided in a bad format"""

    identifiers: List[str] = list("")
