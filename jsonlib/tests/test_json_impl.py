"""표준 json 모듈을 사용하지 않고 직접 구현한 파서/직렬화기(_json_impl) 테스트."""

import pytest

from jsonlib import _json_impl


def test_parse_primitives():
    assert _json_impl.parse("true") is True
    assert _json_impl.parse("false") is False
    assert _json_impl.parse("null") is None
    assert _json_impl.parse("42") == 42
    assert isinstance(_json_impl.parse("42"), int)
    assert _json_impl.parse("-3.5") == -3.5
    assert _json_impl.parse('"hello"') == "hello"


def test_parse_numbers_with_exponent_and_fraction():
    assert _json_impl.parse("1e10") == 1e10
    assert _json_impl.parse("-0.5e-3") == -0.0005
    assert _json_impl.parse("0") == 0
    assert isinstance(_json_impl.parse("0"), int)


def test_parse_nested_object_and_array():
    text = '{"x": {"y": [1, 2, {"z": 3}]}, "list": [1, 2, 3]}'
    assert _json_impl.parse(text) == {
        "x": {"y": [1, 2, {"z": 3}]},
        "list": [1, 2, 3],
    }


def test_parse_empty_object_and_array():
    assert _json_impl.parse("{}") == {}
    assert _json_impl.parse("[]") == []


def test_parse_string_escapes():
    text = r'"tab\tquote\"backslash\\newline\n"'
    assert _json_impl.parse(text) == 'tab\tquote"backslash\\newline\n'


def test_parse_unicode_escape_and_surrogate_pair():
    assert _json_impl.parse(r'"Aé"') == "Aé"
    assert _json_impl.parse(r'"😀"') == "😀"


def test_parse_ignores_surrounding_whitespace():
    assert _json_impl.parse("  \n [1, 2]\t ") == [1, 2]


def test_parse_invalid_json_raises_json_decode_error():
    with pytest.raises(_json_impl.JSONDecodeError):
        _json_impl.parse("{invalid")


def test_parse_extra_data_raises():
    with pytest.raises(_json_impl.JSONDecodeError):
        _json_impl.parse("{}{}")


def test_parse_unterminated_string_raises():
    with pytest.raises(_json_impl.JSONDecodeError):
        _json_impl.parse('"unterminated')


def test_dumps_and_parse_roundtrip():
    data = {
        "name": "홍길동",
        "list": [1, 2.5, None, True, False],
        "nested": {"k": "v"},
    }
    text = _json_impl.dumps(data, indent=2, ensure_ascii=False)
    assert _json_impl.parse(text) == data


def test_dumps_ensure_ascii_escapes_non_ascii():
    text = _json_impl.dumps({"name": "홍길동"}, ensure_ascii=True)
    assert "홍길동" not in text
    assert _json_impl.parse(text) == {"name": "홍길동"}


def test_dumps_unsupported_type_raises_type_error():
    class NotSerializable:
        pass

    with pytest.raises(TypeError):
        _json_impl.dumps({"a": NotSerializable()})


def test_dumps_matches_stdlib_json_semantics():
    import json as stdlib_json

    data = {"a": 1, "b": [1, 2, 3.5, -4, True, False, None, "hi\nthere"]}
    text = _json_impl.dumps(data)
    assert stdlib_json.loads(text) == data
