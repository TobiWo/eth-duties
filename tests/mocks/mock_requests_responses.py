from typing import Any

from requests import Response


class MockResponse:
    def __init__(self, json_data: Any, status_code: int) -> None:
        self.json_data = json_data
        self.status_code = status_code

    def json(self) -> Any:
        return self.json_data


MOCK_GENESIS_RESPONSE = MockResponse({"genesis_time", "1695902400"}, 200)

MOCK_400_RESPONSE = Response()
MOCK_400_RESPONSE.status_code = 400
MOCK_400_RESPONSE = Response()
MOCK_400_RESPONSE.status_code = 400
