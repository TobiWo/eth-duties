"""Module for rest specific types
"""

from enum import Enum


class HttpMethod(Enum):
    """Enum for http methods"""

    POST = "POST"
    DELETE = "DELETE"
