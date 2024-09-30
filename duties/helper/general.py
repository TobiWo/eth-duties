"""General helper module
"""

from datetime import timedelta
from typing import Dict

from cli.types import NodeConnectionProperties
from constants.program import REQUEST_HEADER


def get_correct_request_header(
    node_connection_properties: NodeConnectionProperties,
) -> Dict[str, str]:
    """Get request header in dependence of whether or not to call a validator node

    Args:
        node_connection_properties (NodeConnectionProperties): Object with respective connection information # pylint: disable=line-too-long

    Returns:
        Dict[str, str]: Request header
    """
    if node_connection_properties.bearer_token:
        header_with_authentication = REQUEST_HEADER
        header_with_authentication.update(
            {"Authorization": f"Bearer {node_connection_properties.bearer_token}"}
        )
        return header_with_authentication
    return REQUEST_HEADER


def format_timedelta_to_hours(time_delta: timedelta) -> str:
    """Format a timedelta to HH:MM:SS

    Args:
        time_delta (timedelta): Timedelta which will be formatted

    Returns:
        str: Timedelta in format HH:MM:SS
    """

    def __get_two_digit_time_value(time_value: int) -> str:
        """Format time integer to two digit string

        Args:
            time_value (int): Hours, minutes or seconds

        Returns:
            str: Two digit hours, minutes or seconds
        """
        if time_value < 10:
            return "0" + str(time_value)
        return str(time_value)

    minutes, seconds = divmod(int(time_delta.total_seconds()), 60)
    hours, minutes = divmod(minutes, 60)
    time_values = [hours, minutes, seconds]
    time_string = ":".join(
        [__get_two_digit_time_value(time_value) for time_value in time_values]
    )
    return time_string
