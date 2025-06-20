import re
from enum import Enum

import pytest
import voluptuous as vol

from voluptuous_serialize import UNSUPPORTED, convert


def test_int_schema():
    for value in int, vol.Coerce(int):
        assert {"type": "integer"} == convert(vol.Schema(value))


def test_str_schema():
    for value in str, vol.Coerce(str):
        assert {"type": "string"} == convert(vol.Schema(value))


def test_float_schema():
    for value in float, vol.Coerce(float):
        assert {"type": "float"} == convert(vol.Schema(value))


def test_bool_schema():
    for value in bool, vol.Coerce(bool):
        assert {"type": "boolean"} == convert(vol.Schema(value))


def test_integer_clamp():
    assert {
        "type": "integer",
        "valueMin": 100,
        "valueMax": 1000,
    } == convert(vol.Schema(vol.All(vol.Coerce(int), vol.Clamp(min=100, max=1000))))


def test_length():
    assert {
        "type": "string",
        "lengthMin": 100,
        "lengthMax": 1000,
    } == convert(vol.Schema(vol.All(vol.Coerce(str), vol.Length(min=100, max=1000))))


def test_datetime():
    assert {
        "type": "datetime",
        "format": "%Y-%m-%dT%H:%M:%S.%fZ",
    } == convert(vol.Schema(vol.Datetime()))


def test_in():
    assert {
        "type": "select",
        "options": [
            ("beer", "beer"),
            ("wine", "wine"),
        ],
    } == convert(vol.Schema(vol.In(["beer", "wine"])))


def test_in_dict():
    assert {
        "type": "select",
        "options": [
            ("en_US", "American English"),
            ("zh_CN", "Chinese (Simplified)"),
        ],
    } == convert(
        vol.Schema(
            vol.In({"en_US": "American English", "zh_CN": "Chinese (Simplified)"})
        )
    )


def test_dict():
    assert [
        {
            "name": "name",
            "type": "string",
            "lengthMin": 5,
            "required": True,
        },
        {
            "name": "age",
            "type": "integer",
            "valueMin": 18,
            "required": True,
        },
        {
            "name": "hobby",
            "type": "string",
            "default": "not specified",
            "optional": True,
        },
    ] == convert(
        vol.Schema(
            {
                vol.Required("name"): vol.All(str, vol.Length(min=5)),
                vol.Required("age"): vol.All(vol.Coerce(int), vol.Range(min=18)),
                vol.Optional("hobby", default="not specified"): str,
            }
        )
    )


def test_marker_description():
    assert [
        {
            "name": "name",
            "type": "string",
            "description": "Description of name",
            "required": True,
        }
    ] == convert(
        vol.Schema(
            {
                vol.Required("name", description="Description of name"): str,
            }
        )
    )


def test_lower():
    assert {
        "type": "string",
        "lower": True,
    } == convert(vol.Schema(vol.All(vol.Lower, str)))


def test_upper():
    assert {
        "type": "string",
        "upper": True,
    } == convert(vol.Schema(vol.All(vol.Upper, str)))


def test_capitalize():
    assert {
        "type": "string",
        "capitalize": True,
    } == convert(vol.Schema(vol.All(vol.Capitalize, str)))


def test_title():
    assert {
        "type": "string",
        "title": True,
    } == convert(vol.Schema(vol.All(vol.Title, str)))


def test_strip():
    assert {
        "type": "string",
        "strip": True,
    } == convert(vol.Schema(vol.All(vol.Strip, str)))


def test_email():
    assert {
        "type": "string",
        "format": "email",
    } == convert(vol.Schema(vol.All(vol.Email, str)))


def test_url():
    assert {
        "type": "string",
        "format": "url",
    } == convert(vol.Schema(vol.All(vol.Url, str)))


def test_fqdnurl():
    assert {
        "type": "string",
        "format": "fqdnurl",
    } == convert(vol.Schema(vol.All(vol.FqdnUrl, str)))


def test_maybe():
    assert {
        "type": "string",
        "allow_none": True,
    } == convert(vol.Schema(vol.Maybe(str)))


def test_custom_serializer():
    def custem_serializer(schema):
        if schema is str:
            return {"type": "a string!"}
        return UNSUPPORTED

    assert {
        "type": "a string!",
        "upper": True,
    } == convert(
        vol.Schema(vol.All(vol.Upper, str)), custom_serializer=custem_serializer
    )


def test_constant():
    for value in True, False, "Hello", 1:
        assert {"type": "constant", "value": value} == convert(vol.Schema(value))


def test_enum():
    class TestEnum(Enum):
        ONE = "one"
        TWO = 2

    assert {
        "type": "select",
        "options": [
            ("one", "one"),
            (2, 2),
        ],
    } == convert(vol.Schema(vol.Coerce(TestEnum)))


class UnsupportedClass:
    pass


@pytest.mark.parametrize(
    "unsupported_schema",
    [
        None,
        object,
        list,
        set,
        frozenset,
        tuple,
        UnsupportedClass,
        [],
        vol.IsFalse(),
        vol.IsTrue(),
        vol.Boolean(),
        vol.Any(1, 2, 3, msg="Expected 1 2 or 3"),
        vol.Any("true", "false", vol.All(vol.Any(int, bool), vol.Coerce(bool))),
        vol.Union(
            {"type": "a", "a_val": "1"},
            {"type": "b", "b_val": "2"},
            discriminant=lambda val, alt: filter(
                lambda v: v["type"] == val["type"], alt
            ),
        ),
        vol.Match(r"^0x[A-F0-9]+$"),
        vol.Replace("hello", "goodbye"),
        vol.IsFile(),
        vol.IsDir(),
        vol.PathExists(),
        vol.NotIn(["beer", "wine"]),
        vol.Contains(1),
        vol.ExactSequence([str, int, list, list]),
        vol.Unique(),
        vol.Equal(1),
        vol.Unordered([2, 1]),
        vol.Number(precision=6, scale=2),
        vol.SomeOf(min_valid=2, validators=[vol.Range(1, 5), vol.Any(float, int), 6.6]),
    ],
)
def test_unsupported_schema(unsupported_schema):
    with pytest.raises(
        ValueError,
        # the full error message is matched to make sure
        # the outer schema raised instead of some sub-part
        match=re.escape(f"Unable to convert schema: {unsupported_schema}"),
    ):
        convert(vol.Schema(unsupported_schema))


@pytest.mark.parametrize(
    "unsupported_schema",
    [
        vol.All({"a": int}),
        vol.All(
            vol.Schema({vol.Required("a"): int}),
        ),
        {
            "name": str,
            "position": {
                "lat": float,
                "lon": float,
            },
        },
    ],
)
def test_unsupported_subschema(unsupported_schema):
    with pytest.raises(
        ValueError,
        match=r"^Unable to convert .*schema:",
    ):
        convert(vol.Schema(unsupported_schema))
