"""Defines constants for the api fetcher package
"""

# response json object names
RESPONSE_JSON_DATA_FIELD_NAME = "data"
RESPONSE_JSON_DATA_GENESIS_TIME_FIELD_NAME = "genesis_time"

# api endpoints
ATTESTATION_DUTY_ENDPOINT = "/eth/v1/validator/duties/attester/"
BLOCK_PROPOSING_DUTY_ENDPOINT = "/eth/v1/validator/duties/proposer/"
BEACON_GENESIS_ENDPOINT = "/eth/v1/beacon/genesis"

# error messages
CONNECTION_ERROR_MESSAGE = "Couldn't connect to beacon client. Retry in 2 second."
READ_TIMEOUT_ERROR_MESSAGE = "Couldn't read from beacon client. Retry in 5 seconds."
NO_RESPONSE_ERROR_MESSAGE = "Couldn't fetch any data from the beacon client."
NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE = (
    "Response object does not include a 'data' field"
)

# Protocol and program logic
SLOT_TIME = 12
SLOTS_PER_EPOCH = 32
REQUEST_TIMEOUT = (3, 5)
REQUEST_CONNECTION_ERROR_WAITING_TIME = 2
REQUEST_READ_TIMEOUT_ERROR_WAITING_TIME = 5
YELLOW_PRINTING_THRESHOLD_IN_SECONDS = 120.0
RED_PRINTING_THRESHOLD_IN_SECONDS = 60.0
PRINTER_TIME_FORMAT = "%M:%S"

# printer messages
NEXT_INTERVAL_MESSAGE = "Printing next interval..."
NO_UPCOMING_DUTIES_MESSAGE = "No upcoming duties detected!"
