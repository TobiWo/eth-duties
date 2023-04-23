"""Defines program related constants
"""

from math import floor

from cli.arguments import ARGUMENTS
from helper.terminate import GracefulTerminator

REQUEST_TIMEOUT = (3, 5)
REQUEST_CONNECTION_ERROR_WAITING_TIME = 2
REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME = 5
REQUEST_HEADER = {"Content-type": "application/json", "Accept": "text/plain"}
PRINTER_TIME_FORMAT = "%M:%S"
GRACEFUL_TERMINATOR = GracefulTerminator(
    floor(ARGUMENTS.mode_cicd_waiting_time / ARGUMENTS.interval)
)
THRESHOLD_TO_INFORM_USER_FOR_WAITING_PERIOD = 5000
NOT_ALLOWED_CHARACTERS_FOR_VALIDATOR_PARSING = [".", ","]
NUMBER_OF_VALIDATORS_PER_REST_CALL = 1000
MAX_NUMBER_OF_VALIDATORS_FOR_FETCHING_ATTESTATION_DUTIES = 100
ALIAS_SEPARATOR = ";"
PUBKEY_PREFIX = "0x"
PUBKEY_LENGTH = 48
