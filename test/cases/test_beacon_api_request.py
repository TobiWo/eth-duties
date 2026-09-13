"""Tests for beacon API request response handling."""

import asyncio
import logging as std_logging
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from requests import Response

DUTIES_PATH = Path(__file__).resolve().parents[2] / "duties"
sys.path.insert(0, str(DUTIES_PATH))
sys.argv = [
    "test_beacon_api_request.py",
    "--validators",
    "1",
    "--beacon-nodes",
    "http://127.0.0.1:1",
]
std_logging.disable(std_logging.CRITICAL)

# pylint: disable-next=wrong-import-position
from cli.types import NodeConnectionProperties, NodeType
# pylint: disable-next=wrong-import-position
from constants import endpoints
# pylint: disable-next=wrong-import-position
from helper.error import NoDataFromEndpointError
# pylint: disable-next=wrong-import-position
from protocol import request

std_logging.disable(std_logging.NOTSET)
sys.argv = ["test_beacon_api_request.py"]


def _make_response(
    body: str, status_code: int = 200, content_type: str = "application/json"
) -> Response:
    response = Response()
    response.status_code = status_code
    response._content = body.encode("utf-8")  # pylint: disable=protected-access
    response.headers["Content-Type"] = content_type
    response.raw = Mock()
    return response


class BeaconApiRequestTest(unittest.TestCase):
    """Test beacon API request handling."""

    def test_block_proposing_duty_endpoint_uses_v2(self) -> None:
        """Proposing duties are fetched through the v2 Beacon API endpoint."""
        self.assertEqual(
            endpoints.BLOCK_PROPOSING_DUTY_ENDPOINT,
            "/eth/v2/validator/duties/proposer/",
        )

    def test_v2_proposer_response_returns_data_items(self) -> None:
        """Top-level v2 metadata does not change the returned duty data."""
        response = _make_response(
            (
                '{"dependent_root":"0x1234","execution_optimistic":false,'
                '"data":[{"pubkey":"0xabcd","validator_index":"1","slot":"2"}]}'
            )
        )

        convert_to_raw_data_responses = getattr(
            request, "__convert_to_raw_data_responses"
        )

        data = convert_to_raw_data_responses([response], flatten=True)

        self.assertEqual(
            data,
            [{"pubkey": "0xabcd", "validator_index": "1", "slot": "2"}],
        )

    def test_non_json_response_returns_no_data_after_retries(self) -> None:
        """Plain text upstream responses do not escape as JSON decode errors."""
        node = NodeConnectionProperties("http://beacon.example", NodeType.BEACON)
        non_json_response = _make_response(
            "404 page not found",
            status_code=404,
            content_type="text/plain; charset=utf-8",
        )

        async def run_request() -> Response:
            handle_api_request = getattr(request, "__handle_api_request")
            return await handle_api_request(
                node,
                "/eth/v2/validator/duties/proposer/0",
                request.CalldataType.NONE,
                [],
            )

        with patch.object(
            request, "__send_api_request", return_value=non_json_response
        ), self.assertLogs(level="ERROR") as log_context:
            response = asyncio.run(run_request())

        joined_logs = "\n".join(log_context.output)
        self.assertIn("Beacon node returned non-JSON response", joined_logs)
        self.assertIn("status=404", joined_logs)
        self.assertIn("content-type=text/plain; charset=utf-8", joined_logs)
        self.assertIn("404 page not found", joined_logs)

        with self.assertRaises(NoDataFromEndpointError):
            convert_to_raw_data_responses = getattr(
                request, "__convert_to_raw_data_responses"
            )
            convert_to_raw_data_responses([response], flatten=True)


if __name__ == "__main__":
    unittest.main()
