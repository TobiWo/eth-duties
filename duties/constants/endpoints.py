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
FEERECIPIENT_ENDPOINT = "/eth/v1/validator/0xb07020250b69aebcaca7dbc00dfa73d2c8519ded7ec8afff3e4750414aacd6c0b3d5273cf89b504d51fb9b3e209b9c9e/feerecipient"  # pylint: disable=line-too-long
