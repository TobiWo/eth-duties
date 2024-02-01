"""Module with helper functions to parse specific cli arguments
"""

from typing import List

from duties.constants.program import HEX_COLOR_STARTING_POSITIONS, HEX_TO_INT_BASE


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


def set_logging_color(logging_color: str) -> List[int]:
    """Parse provided logging color

    Args:
        logging_color (str): Logging color in hex or RGB code

    Raises:
        ValueError: Error if RGB codes are not in range 0-255

    Returns:
        List[int]: RGB color code
    """
    if logging_color.startswith("#"):
        logging_color = logging_color[1:]
        rgb_color_codes = [
            int(logging_color[position : position + 2], HEX_TO_INT_BASE)
            for position in HEX_COLOR_STARTING_POSITIONS
        ]
    else:
        string_rgb_color_codes = logging_color.split(",")
        rgb_color_codes = [int(rgb_code) for rgb_code in string_rgb_color_codes]
    filtered_rgb_color_codes = [
        rgb_code for rgb_code in rgb_color_codes if rgb_code >= 0 if rgb_code <= 255
    ]
    if len(filtered_rgb_color_codes) != 3:
        raise ValueError()
    return filtered_rgb_color_codes
