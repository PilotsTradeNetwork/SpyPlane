import json
from pathlib import Path


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json.loads(json_data)
        self.status_code = status_code
        self.ok = status_code < 300

    async def json(self):
        return self.json_data

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


dirname = Path(__file__).parent


def mocked_requests_get(*args, **kwargs):
    if args[0] == "https://elitebgs.app/api/ebgs/v5/systems" and kwargs["params"]["name"] == "Wally Bei":
        return load_file_as_response("none_states_system")
    if args[0] == "https://elitebgs.app/api/ebgs/v5/systems" and kwargs["params"]["name"] == "Beatis":
        return load_file_as_response("interesting_states_system")
    return MockResponse(None, 404)


def load_file_as_response(filename):
    with (dirname / f"{filename}.json").open() as data:
        return MockResponse(data.read(), 200)
