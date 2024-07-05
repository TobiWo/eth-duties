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


class NodeType(Enum):
    """Defines the type of node"""

    BEACON = "beacon"
    VALIDATOR = "validator"


@dataclass(frozen=True)
class NodeConnectionProperties:
    """Necessary properties to connect to an Ethereum Consensus Layer node
    (beacon node or validator)"""

    url: str
    node_type: NodeType
    bearer_token: str | None = None
