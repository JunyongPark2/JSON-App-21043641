import pytest

import jsonlib


def test_loads_and_dumps_roundtrip():
    data = {"name": "홍길동", "age": 30, "items": [1, 2, 3]}
    text = jsonlib.dumps(data)
    assert jsonlib.loads(text) == data


def test_loads_invalid_raises():
    with pytest.raises(jsonlib.JsonParseError):
        jsonlib.loads("{invalid json")


def test_save_and_load_file(tmp_path):
    data = {"a": 1, "nested": {"b": [1, 2, 3]}}
    file_path = tmp_path / "sub" / "data.json"

    jsonlib.save(data, file_path)
    loaded = jsonlib.load(file_path)

    assert loaded == data


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(jsonlib.JsonParseError):
        jsonlib.load(tmp_path / "missing.json")


def test_save_unserializable_raises(tmp_path):
    class NotSerializable:
        pass

    with pytest.raises(jsonlib.JsonSaveError):
        jsonlib.save({"obj": NotSerializable()}, tmp_path / "bad.json")
