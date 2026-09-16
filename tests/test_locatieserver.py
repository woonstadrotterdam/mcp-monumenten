"""Tests for PDOK Locatieserver provincie lookup."""

from typing import Any

import pytest

from mcp_monumenten.locatieserver import lookup_provincie, provincienaam_from_payload

COOLSINGEL_VBO_ID = "0599010000243626"


def test_provincienaam_from_payload_reads_first_doc() -> None:
    payload = {"response": {"docs": [{"provincienaam": "Zuid-Holland"}]}}
    assert provincienaam_from_payload(payload) == "Zuid-Holland"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"response": {}},
        {"response": {"docs": []}},
        {"response": {"docs": [{}]}},
        {"response": {"docs": [{"provincienaam": ""}]}},
        {"response": {"docs": ["Zuid-Holland"]}},
    ],
)
def test_provincienaam_from_payload_missing(payload: dict[str, Any]) -> None:
    assert provincienaam_from_payload(payload) is None


class _FakeResponse:
    def __init__(self, status: int, payload: object) -> None:
        self.status = status
        self._payload = payload

    async def json(self) -> object:
        return self._payload

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _FakeSession:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    def get(self, url: str, params: object = None) -> _FakeResponse:
        return self._response

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class _BoomSession:
    async def __aenter__(self) -> "_BoomSession":
        raise ConnectionError("locatieserver unavailable")

    async def __aexit__(self, *args: object) -> None:
        return None


@pytest.mark.asyncio
async def test_lookup_provincie_returns_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"response": {"docs": [{"provincienaam": "Noord-Holland"}]}}
    monkeypatch.setattr(
        "mcp_monumenten.locatieserver.aiohttp.ClientSession",
        lambda *args, **kwargs: _FakeSession(_FakeResponse(200, payload)),
    )
    assert await lookup_provincie(COOLSINGEL_VBO_ID) == "Noord-Holland"


@pytest.mark.asyncio
async def test_lookup_provincie_http_error_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_monumenten.locatieserver.aiohttp.ClientSession",
        lambda *args, **kwargs: _FakeSession(_FakeResponse(500, {})),
    )
    assert await lookup_provincie(COOLSINGEL_VBO_ID) is None


@pytest.mark.asyncio
async def test_lookup_provincie_exception_is_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "mcp_monumenten.locatieserver.aiohttp.ClientSession",
        lambda *args, **kwargs: _BoomSession(),
    )
    assert await lookup_provincie(COOLSINGEL_VBO_ID) is None


@pytest.mark.asyncio
async def test_lookup_provincie_coolsingel_is_zuid_holland() -> None:
    """Live Locatieserver lookup for Coolsingel 30."""
    assert await lookup_provincie(COOLSINGEL_VBO_ID) == "Zuid-Holland"
