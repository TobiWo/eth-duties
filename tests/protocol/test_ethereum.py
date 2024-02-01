from unittest.mock import patch

from pytest_mock import MockerFixture

from duties.protocol.ethereum import get_current_slot
from tests.mocks.mock_arguments import MOCK_STANDARD_ARGUMENTS
from tests.mocks.mock_requests_responses import MOCK_GENESIS_RESPONSE


@patch(
    target="duties.protocol.connection.get_arguments",
    return_value=MOCK_STANDARD_ARGUMENTS,
)
@patch("duties.protocol.ethereum.time", return_value=1695902412.0)
def test_get_healthy_beacon_node(
    time_mock: MockerFixture, arguments_mock: MockerFixture
) -> None:
    with patch("duties.protocol.ethereum.send_beacon_api_request") as mock_request:
        mock_request.return_value = MOCK_GENESIS_RESPONSE
        expected_slot = 1
        assert expected_slot == get_current_slot()
