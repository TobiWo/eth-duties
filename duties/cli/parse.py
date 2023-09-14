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


def set_beacon_node_urls(beacon_node_urls: str) -> List[str]:
    """Parse the beacon node urls

    Args:
        beacon_node_urls (str): Provided beacon node urls

    Raises:
        ValueError: Error if one or many provided urls do not start with http:// or https://

    Returns:
        List[str]: Parsed beacon node urls
    """
    splitted_urls = []
    if "," in beacon_node_urls:
        splitted_urls = beacon_node_urls.split(",")
        splitted_urls = [
            url for url in splitted_urls if url.startswith(("http://", "https://"))
        ]
        if len(splitted_urls) != len(beacon_node_urls.split(",")):
            raise ValueError()
        return splitted_urls
    if not beacon_node_urls.startswith(("http://", "https://")):
        raise ValueError()
    return [beacon_node_urls]
