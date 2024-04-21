"""Module for argument parser related types
"""

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    """Defines the mode at which eth-duties will run"""

    LOG = "log"
    NO_LOG = "no-log"
    CICD_EXIT = "cicd-exit"
    CICD_WAIT = "cicd-wait"
    CICD_FORCE_GRACEFUL_EXIT = "cicd-force-graceful-exit"


@dataclass
class NodeConnectionInformation:
    """Information to connect to an Ethereum node"""

    url: str


@dataclass
class ValidatorConnectionInformation(NodeConnectionInformation):
    """Bearer token to authenticate at the validator (key manager) api"""

    bearer_token: str
