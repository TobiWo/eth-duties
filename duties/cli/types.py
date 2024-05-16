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
class NodeConnectionProperties:
    """Necessary properties to connect to an Ethereum Consensus Layer node
    (beacon node or validator)"""

    url: str
    bearer_token: str | None = None
