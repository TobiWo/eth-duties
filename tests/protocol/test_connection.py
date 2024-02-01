from unittest.mock import patch

from pytest_mock import MockerFixture

from duties.protocol.connection import BeaconNode
from tests.mocks.mock_arguments import MOCK_STANDARD_ARGUMENTS


@patch(
    target="duties.protocol.connection.get_arguments",
    return_value=MOCK_STANDARD_ARGUMENTS,
)
def test_get_healthy_beacon_node(arguments_mock: MockerFixture) -> None:
    beacon_node = BeaconNode()
    arguments_mock.return_value.beacon_nodes = [
        "http://localhost:5052",
        "http://localhost:5051",
    ]
    with patch("duties.protocol.connection.get") as mock_request:
        mock_request.return_value.status_code = 200
        returned_beacon_node = beacon_node.get_healthy_beacon_node(True)
        expected_beacon_node = MOCK_STANDARD_ARGUMENTS.beacon_nodes[0]
        assert expected_beacon_node == returned_beacon_node
        assert beacon_node.is_any_node_healthy == True

        mock_request.return_value.status_code = 400
        returned_beacon_node = beacon_node.get_healthy_beacon_node(True)
        expected_beacon_node = MOCK_STANDARD_ARGUMENTS.beacon_nodes[0]
        assert expected_beacon_node == returned_beacon_node
        assert beacon_node.is_any_node_healthy == False
        assert beacon_node.is_any_node_healthy == False
