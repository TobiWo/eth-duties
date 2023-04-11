"""Module with helper functions to parse specific cli arguments
"""

from typing import List


def parse_validator_identifiers(validators: str) -> List[str]:
    """Parses provided validators for space and comma separation

    Args:
        validators (str): User provided validators

    Returns:
        List[str]: Parsed validators
    """
    if "," in validators:
        return validators.split(",")
    return validators.split()
