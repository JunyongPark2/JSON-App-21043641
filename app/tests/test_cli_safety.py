"""안전성(Safety) 테스트.

사용자의 실수나 잘못된 입력으로 데이터가 훼손/유실되지 않는지 검증한다.
"""

import pytest

from app import cli
from app.storage import RecordStore


def feed_input(monkeypatch, values):
    """input()이 순서대로 values를 반환하도록 패치한다."""
    values_iter = iter(values)
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(values_iter))


def test_delete_cancelled_keeps_record(tmp_path, monkeypatch):
    """삭제 확인에서 'y'가 아니면 데이터가 그대로 남아야 한다."""
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})

    feed_input(monkeypatch, [str(record["id"]), "n"])
    cli.do_delete(store)

    assert store.find_by_id(record["id"]) is not None


def test_delete_confirmed_removes_record(tmp_path, monkeypatch):
    """'y'로 확인해야만 실제로 삭제된다."""
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})

    feed_input(monkeypatch, [str(record["id"]), "y"])
    cli.do_delete(store)

    assert store.find_by_id(record["id"]) is None


def test_delete_missing_id_does_not_raise(tmp_path, monkeypatch):
    """존재하지 않는 ID를 삭제하려 해도 예외 없이 안전하게 처리되어야 한다."""
    store = RecordStore(tmp_path / "db.json")

    feed_input(monkeypatch, ["999"])
    cli.do_delete(store)  # 예외가 발생하면 테스트 실패


def test_delete_non_numeric_id_is_rejected_safely(tmp_path, monkeypatch):
    """숫자가 아닌 ID 입력 시 예외 없이 안전하게 취소되어야 한다."""
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})

    feed_input(monkeypatch, ["abc"])
    cli.do_delete(store)

    assert store.find_by_id(record["id"]) is not None


def test_update_cannot_change_id(tmp_path, monkeypatch):
    """id 필드는 update 입력을 통해서도 변경될 수 없어야 한다."""
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})
    original_id = record["id"]

    feed_input(monkeypatch, [str(original_id), "id=999", "name=Alicia", ""])
    cli.do_update(store)

    updated = store.find_by_id(original_id)
    assert updated is not None
    assert updated["id"] == original_id
    assert updated["name"] == "Alicia"
    assert store.find_by_id(999) is None


def test_update_missing_id_does_not_raise(tmp_path, monkeypatch):
    """존재하지 않는 ID를 수정하려 해도 예외 없이 안전하게 처리되어야 한다."""
    store = RecordStore(tmp_path / "db.json")

    feed_input(monkeypatch, ["999"])
    cli.do_update(store)  # 예외가 발생하면 테스트 실패


def test_create_with_empty_input_does_not_save_blank_record(tmp_path, monkeypatch):
    """빈 입력만으로는 빈 레코드가 저장되지 않아야 한다."""
    store = RecordStore(tmp_path / "db.json")

    feed_input(monkeypatch, [""])
    cli.do_create(store)

    assert store.read_all() == []


def test_save_failure_does_not_corrupt_existing_file(tmp_path):
    """직렬화 실패 시 기존 파일 내용이 손상되지 않아야 한다."""
    import jsonlib

    path = tmp_path / "db.json"
    jsonlib.save({"safe": "data"}, path)

    class NotSerializable:
        pass

    with pytest.raises(jsonlib.JsonSaveError):
        jsonlib.save({"bad": NotSerializable()}, path)

    assert jsonlib.load(path) == {"safe": "data"}


def test_save_leaves_no_temp_file_behind(tmp_path):
    """정상 저장 후에는 임시 파일이 남아있지 않아야 한다."""
    import jsonlib

    path = tmp_path / "db.json"
    jsonlib.save({"a": 1}, path)

    leftovers = [p for p in tmp_path.iterdir() if p.name != "db.json"]
    assert leftovers == []
