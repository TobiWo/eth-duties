"""Module for argument parser related types
"""

from enum import Enum


class Mode(Enum):
    """Defines the mode at which eth-duties will run"""

    LOG = "log"
    NO_LOG = "no-log"
    CICD_EXIT = "cicd-exit"
    CICD_WAIT = "cicd-wait"
    CICD_FORCE_GRACEFUL_EXIT = "cicd-force-graceful-exit"
