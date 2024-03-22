"""Module with functions to test eth-duties startup
"""

# pylint: disable-next=import-error
from constants.logging import CONNECTION_ERROR_MESSAGE, NO_AVAILABLE_BEACON_NODE_MESSAGE
from test_helper.config import CONFIG
from test_helper.functions import run_generic_test
from test_helper.general import get_general_eth_duties_start_command


def test_no_beacon_connection_at_startup() -> int:
    """Test no present beacon node connection at startup

    Returns:
        int: Whether or not test succeeds while 1 is success and 0 is failure
    """
    expected_logs = [CONNECTION_ERROR_MESSAGE, NO_AVAILABLE_BEACON_NODE_MESSAGE]
    command = get_general_eth_duties_start_command(
        CONFIG.validators.active.general, CONFIG.general.failing_beacon_node_url
    )
    return run_generic_test(
        expected_logs, command, "no beacon connection at startup", expected_logs[0]
    )
