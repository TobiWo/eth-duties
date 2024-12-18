"""Defines logging messages
"""

CONNECTION_ERROR_MESSAGE = (
    "Couldn't connect to %s node with url: %s. Retry in 2 second."
)
READ_TIMEOUT_ERROR_MESSAGE = (
    "Couldn't read from %s node with url: %s. Retry in 5 seconds."
)
NO_RESPONSE_ERROR_MESSAGE = "Couldn't fetch any data from client: %s"
NO_FETCHED_VALIDATOR_IDENTIFIERS_MESSAGE = (
    "Validator identifiers could not be fetched from client: %s"
)
NO_DATA_FIELD_IN_RESPONS_JSON_ERROR_MESSAGE = (
    "Response object does not include a 'data' field"
)
SYSTEM_EXIT_MESSAGE = "Detected user intervention (SIGINT). Shutting down."
NEXT_INTERVAL_MESSAGE = "Logging next duties interval..."
NO_UPCOMING_DUTIES_MESSAGE = "No upcoming duties detected!"
TOO_MANY_PROVIDED_VALIDATORS_FOR_FETCHING_ATTESTATION_DUTIES_MESSAGE = (
    "Provided number of validators for fetching attestion duties is high (> %s). "
    "This pollutes the console output and prevents checking important duties. "
    "Checking attestion duties will be skipped! "
    "To increase the max. number of logged attestation duties use '--max-attestation-duty-logs'"
)
HIGHER_PROCESSING_TIME_INFO_MESSAGE = (
    "You provided %s validators. Fetching all necessary data may take some time."
)
INACTIVE_VALIDATORS_MESSAGE = (
    "The following provided validators are not active "
    "and therefore will be skipped for further processing: %s"
)
SKIPPING_PROVIDED_IDENTIFIER_MESSAGE = (
    "Skipping provided validator %s for further processing due to bad format"
)
WRONG_OR_INCOMPLETE_PUBKEY_MESSAGE = "Wrong or incomplete provided pubkey: 0x%s"
PUBKEY_IS_NOT_HEXADECIMAL_MESSAGE = "Pubkey 0x%s is not hexadecimal: %s"
DUPLICATE_VALIDATORS_MESSAGE = (
    "Filtered duplicated validators with different identifiers: %s"
)
ACTIVATED_MODE_MESSAGE = "Started in mode: %s"
PROPORTION_OF_DUTIES_ABOVE_TIME_THRESHOLD_MESSAGE = (
    "%s%% of %s duties will be executed in %s sec. or later"
)
EXIT_CODE_MESSAGE = "Exiting with code: %d"
EXIT_DUE_TO_MAX_WAITING_TIME_MESSAGE = "Reached max. waiting time for mode 'cicd-wait'"
MAIN_EXIT_MESSAGE = "Happy staking. See you for next maintenance \U0001F642 !"
START_REST_SERVER_MESSAGE = "Started rest api server on localhost:%s"
NOT_SUPPORTED_HTTP_METHOD_MESSAGE = "HTTP method %s is not supported yet"
CANNOT_READ_SHARED_MEMORY_MESSAGE = "Could not read from shared memory. Exiting!"
CANNOT_WRITE_SHARED_MEMORY_MESSAGE = "Could not write to shared memory. Exiting!"
PORT_ALREADY_IN_USAGE_MESSAGE = (
    "Port %s is already in use. Starting eth-duties without rest server."
)
IGNORED_REST_FLAG_MESSAGE = (
    "Rest server will not be started in any cicd-mode. Flag '--rest' will be ignored!"
)
MODIFIED_VALIDATOR_IDENTIFIER_MESSAGE = "%s validator identifiers: %s"
NO_AVAILABLE_BEACON_NODE_MESSAGE = (
    "Non of the provided beacon nodes is ready to accept requests"
)
USED_BEACON_NODE_MESSAGE = "Using beacon node %s"
PRIMARY_BEACON_NODE_DOWN_MESSAGE = (
    "Primary beacon node %s is not ready to accept requests"
)
TRYING_BACKUP_NODES_MESSAGE = "Trying backup nodes"
NODE_URL_ERROR_MESSAGE = "{0} node url should start with http or https"
VALIDATOR_NODE_PROPERTY_ERROR_MESSAGE = (
    "Validator node information should only consist of url "
    "and bearer token separated by semicolon"
)
UPDATE_VALIDATOR_IDENTIFIER_MESSAGE = (
    "Updating validator identifier status and identifiers fetched from provided "
    "validator nodes"
)
LOADED_VALIDATOR_IDENTIFIER_MESSAGE = (
    "Loaded %s validator identifiers from provided validator nodes"
)
ALL_HEALTHY_VALIDATOR_NODES_MESSAGE = "All validator keymanager endpoints are healthy"
NO_HEALTHY_VALIDATOR_NODES_MESSAGE = (
    "None of the provided validator nodes is reachable! List of duties will be empty "
    "after the next identifier and status update (see --validator-update-interval)"
)
ONE_NON_HEALTHY_VALIDATOR_NODE_MESSAGE = (
    "Validator node %s is not reachable! No duties will be displayed for the related validators "
    "after the next identifier and status update (see --validator-update-interval)"
)
VALIDATOR_NODE_AUTHORIZATION_FAILED_MESSAGE = (
    "Authentication failed for validator node: %s"
)
