"""Defines program related constants
"""

from helper.killer import GracefulKiller

REQUEST_TIMEOUT = (3, 5)
REQUEST_CONNECTION_ERROR_WAITING_TIME = 2
REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME = 5
YELLOW_PRINTING_THRESHOLD_IN_SECONDS = 120.0
RED_PRINTING_THRESHOLD_IN_SECONDS = 60.0
PRINTER_TIME_FORMAT = "%M:%S"
GRACEFUL_KILLER = GracefulKiller()
