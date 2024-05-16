"""Defines api endpoints
"""

# Beacon API endpoints
ATTESTATION_DUTY_ENDPOINT = "/eth/v1/validator/duties/attester/"
SYNC_COMMITTEE_DUTY_ENDPOINT = "/eth/v1/validator/duties/sync/"
BLOCK_PROPOSING_DUTY_ENDPOINT = "/eth/v1/validator/duties/proposer/"
BEACON_GENESIS_ENDPOINT = "/eth/v1/beacon/genesis"
VALIDATOR_STATUS_ENDPOINT = "/eth/v1/beacon/states/head/validators"
NODE_HEALTH_ENDPOINT = "/eth/v1/node/health"

# Validator key manager API endpoints
LOCAL_KEYSTORES_ENDPOINT = "/eth/v1/keystores"
REMOTE_KEYSTORES_ENDPOINT = "/eth/v1/remotekeys"
