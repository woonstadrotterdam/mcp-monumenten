"""Tests for monumental status result shape."""

from mcp_monumenten.models import MonumentalStatus


def test_provinciaal_monument_is_present_and_null() -> None:
    status = MonumentalStatus(bag_verblijfsobject_id="0599010000243626")
    dumped = status.model_dump()
    assert dumped["provinciaal_monument"] is None
    assert dumped["provincie"] is None
    assert "notitie" not in dumped


def test_provinciaal_monument_schema_says_not_looked_up() -> None:
    schema = MonumentalStatus.model_json_schema()
    description = schema["properties"]["provinciaal_monument"]["description"]
    assert "not looked up" in description
    assert "Noord-Holland" in description
    assert "Drenthe" in description


def test_rijksbeschermd_gezicht_schema_is_national_only() -> None:
    schema = MonumentalStatus.model_json_schema()
    description = schema["properties"]["rijksbeschermd_gezicht"]["description"]
    assert "national" in description.lower()
    assert "municipal" in description
