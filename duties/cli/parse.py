"""Module with helper functions to parse specific cli arguments
"""

from pathlib import Path
from typing import List

from cli.types import NodeConnectionProperties, NodeType
from constants.logging import (
    NODE_URL_ERROR_MESSAGE,
    VALIDATOR_NODE_PROPERTY_ERROR_MESSAGE,
)
from constants.program import (
    HEX_COLOR_STARTING_POSITIONS,
    HEX_TO_INT_BASE,
    MANDATORY_NODE_URL_PREFIXES,
)


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


def set_beacon_nodes(beacon_node_urls: str) -> List[NodeConnectionProperties]:
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
            url for url in splitted_urls if url.startswith(MANDATORY_NODE_URL_PREFIXES)
        ]
        if len(splitted_urls) != len(beacon_node_urls.split(",")):
            raise KeyError(NODE_URL_ERROR_MESSAGE.format(NodeType.BEACON.value))
        return [
            NodeConnectionProperties(beacon_node_url, NodeType.BEACON)
            for beacon_node_url in splitted_urls
        ]
    if not beacon_node_urls.startswith(MANDATORY_NODE_URL_PREFIXES):
        raise KeyError(NODE_URL_ERROR_MESSAGE.format(NodeType.BEACON.value))
    return [NodeConnectionProperties(beacon_node_urls, NodeType.BEACON)]


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


def set_validator_nodes(file_path: str) -> List[NodeConnectionProperties]:
    """Parse provided validator node file

    Args:
        file_path (str): Path to validator node file

    Returns:
        List[ValidatorNode]: Validator node objects
        with respective connection information
    """
    with open(Path(file_path), "r", encoding="utf-8") as validator_nodes_file:
        raw_validator_nodes = validator_nodes_file.readlines()
    validator_nodes = [
        __parse_validator_node(raw_validator_node)
        for raw_validator_node in raw_validator_nodes
    ]
    return validator_nodes


def __parse_validator_node(raw_validator_node: str) -> NodeConnectionProperties:
    """Parse raw validator node properties

    Args:
        raw_validator_node (str): Line in file with validator node information

    Raises:
        ValueError: Error if too many node informations provided and
        the node url does not start with http or https

    Returns:
        ValidatorNode: Validator node object
        with respective connection information
    """
    raw_validator_node_properties = raw_validator_node.split(";")
    if not len(raw_validator_node_properties) == 2:
        raise IndexError(VALIDATOR_NODE_PROPERTY_ERROR_MESSAGE)
    if not raw_validator_node_properties[0].startswith(MANDATORY_NODE_URL_PREFIXES):
        raise KeyError(NODE_URL_ERROR_MESSAGE.format(NodeType.VALIDATOR.value))
    return NodeConnectionProperties(
        raw_validator_node_properties[0],
        NodeType.VALIDATOR,
        raw_validator_node_properties[1].rstrip("\n"),
    )
