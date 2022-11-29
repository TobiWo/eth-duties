"""Defines ethereum related constants and functions
"""

from math import trunc
from time import time

SLOT_TIME = 12
SLOTS_PER_EPOCH = 32
EPOCHS_PER_SYNC_COMMITTEE = 256


def get_current_slot(genesis_time: int) -> int:
    """
    Calculates the current beacon chain slot

    Returns:
        int: The current beacon chain slot
    """
    return trunc((time() - genesis_time) / SLOT_TIME)


def get_current_epoch(genesis_time: int) -> int:
    """Calculates the current epoch based on connected chain specifics

    Returns:
        int: Current epoch
    """
    now = time()
    return trunc((now - genesis_time) / (SLOTS_PER_EPOCH * SLOT_TIME))
