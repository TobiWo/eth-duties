"""Defines logging messages
"""

CONNECTION_ERROR_MESSAGE = "Couldn't connect to beacon client. Retry in 2 second."
READ_TIMEOUT_ERROR_MESSAGE = "Couldn't read from beacon client. Retry in 5 seconds."
NO_RESPONSE_ERROR_MESSAGE = "Couldn't fetch any data from the beacon client."
NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE = (
    "Response object does not include a 'data' field"
)
SYSTEM_EXIT_MESSAGE = "Detected user intervention (SIGINT). Shutting down."
NEXT_INTERVAL_MESSAGE = "Printing next interval..."
NO_UPCOMING_DUTIES_MESSAGE = "No upcoming duties detected!"
TOO_MANY_PROVIDED_VALIDATORS_MESSAGE = (
    "Provided number of validator indices is higher than 300. "
    "This surpasses the current maximum for fetching attestation and sync committee duties. "
    "Checking for those duties will be skipped!"
)
