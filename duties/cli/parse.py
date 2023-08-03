"""Module with helper functions to parse specific cli arguments
"""

from typing import List


def set_validator_identifiers(validators: str) -> List[str]:
    """Parse provided validators for space and comma separation

    Args:
        validators (str): User provided validators

    Returns:
        List[str]: Parsed validators
    """
    if "," in validators:
        return validators.split(",")
    return validators.split()


def set_beacon_node_url(beacon_node_url: str) -> str:
    """Parse the beacon node url

    Args:
        beacon_node_url (str): Beacon node url

    Raises:
        ValueError: Error if provided url does not start with http/https

    Returns:
        str: Beacon node url
    """
    if not beacon_node_url.startswith("http"):
        raise ValueError()
    return beacon_node_url
