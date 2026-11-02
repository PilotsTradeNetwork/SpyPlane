import unittest
from unittest.mock import patch

import httpx

from ptn.spyplane.services import edsm_service
from ptn.spyplane.services.edsm_service import fetch_edsm_systems

MODULE = "ptn.spyplane.services.edsm_service"
RealAsyncClient = httpx.AsyncClient


def _mock_client(handler):
    """Patch httpx.AsyncClient in edsm_service so requests go to *handler* instead of the network."""
    return patch(
        f"{MODULE}.httpx.AsyncClient",
        lambda **kwargs: RealAsyncClient(transport=httpx.MockTransport(handler), **kwargs),
    )


class FetchEdsmSystemsTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_input_makes_no_request(self):
        def handler(_request):
            raise AssertionError("no request expected")

        with _mock_client(handler):
            self.assertEqual(await fetch_edsm_systems([]), {})

    async def test_parses_entries_case_insensitively(self):
        def handler(request):
            self.assertEqual(request.url.params.get_list("systemName[]"), ["sol", "Nowhere", "Achenar"])
            self.assertEqual(request.url.params["showCoordinates"], "1")
            return httpx.Response(
                200,
                json=[
                    {"name": "Sol", "coords": {"x": 0, "y": 0, "z": 0}, "information": {"faction": "x"}},
                    {"name": "Achenar", "coords": {"x": 3, "y": 4, "z": 0}, "information": []},
                ],
            )

        with _mock_client(handler):
            result = await fetch_edsm_systems(["sol", "Nowhere", "Achenar"])

        self.assertEqual(set(result), {"sol", "Nowhere", "Achenar"})
        self.assertIsNone(result["Nowhere"])
        self.assertEqual(result["sol"].name, "Sol")
        self.assertEqual(result["sol"].coords, (0, 0, 0))
        self.assertTrue(result["sol"].is_populated)
        self.assertEqual(result["Achenar"].distance, 5)
        self.assertFalse(result["Achenar"].is_populated)

    async def test_requests_are_chunked(self):
        names = [f"Sys {i}" for i in range(edsm_service.EDSM_CHUNK_SIZE * 2 + 1)]
        chunk_sizes = []

        def handler(request):
            requested = request.url.params.get_list("systemName[]")
            chunk_sizes.append(len(requested))
            return httpx.Response(200, json=[{"name": n, "coords": {"x": 1, "y": 0, "z": 0}} for n in requested])

        with _mock_client(handler):
            result = await fetch_edsm_systems(names)

        size = edsm_service.EDSM_CHUNK_SIZE
        self.assertEqual(chunk_sizes, [size, size, 1])
        self.assertTrue(all(result[n] is not None for n in names))

    async def test_failed_chunk_does_not_drop_others(self):
        names = [f"Sys {i}" for i in range(edsm_service.EDSM_CHUNK_SIZE + 1)]
        calls = 0

        def handler(request):
            nonlocal calls
            calls += 1
            if calls == 1:
                return httpx.Response(500)
            requested = request.url.params.get_list("systemName[]")
            return httpx.Response(200, json=[{"name": n, "coords": {"x": 1, "y": 0, "z": 0}} for n in requested])

        with _mock_client(handler):
            result = await fetch_edsm_systems(names)

        self.assertTrue(all(result[n] is None for n in names[:-1]))
        self.assertIsNotNone(result[names[-1]])

    async def test_empty_object_response_and_bad_coords(self):
        responses = iter(
            [
                httpx.Response(200, json={}),  # EDSM returns {} when nothing matches
                httpx.Response(200, json=[{"name": "Broken", "coords": {"x": 1}}, {"name": "NoCoords"}]),
            ]
        )

        with _mock_client(lambda _request: next(responses)):
            self.assertEqual(await fetch_edsm_systems(["Ghost"]), {"Ghost": None})
            result = await fetch_edsm_systems(["Broken", "NoCoords"])

        self.assertIsNone(result["Broken"].coords)
        self.assertEqual(result["Broken"].distance, 0)
        self.assertIsNone(result["NoCoords"].coords)


if __name__ == "__main__":
    unittest.main()
