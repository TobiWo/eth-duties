"""Module for custom errors
"""


class PrysmError(Exception):
    """Exception raised for specific remote keystore request handling (returning 500)
    by prysm validator client.

    Args:
        message (str): Error message
    """

    def __init__(
        self, message: str = "Remote keystore request sent to prysm which returns 500"
    ) -> None:
        self.message = message
        super().__init__(self.message)
