"""Helper module
"""

from typing import Callable

from fetcher.data_types import ValidatorDuty

sort_duties: Callable[[ValidatorDuty], int] = lambda duty: duty.slot
