"""회귀(Regression) 테스트.

기능 추가/리팩터링 이후에도 기존 CRUD 동작과 데이터 영속성이
깨지지 않는지 확인한다.
"""

import jsonlib
from app.storage import RecordStore


def test_full_crud_lifecycle(tmp_path):
    """Create -> Read -> Update -> Delete -> Read 전체 흐름이 일관되게 동작해야 한다."""
    path = tmp_path / "db.json"
    store = RecordStore(path)

    alice = store.create({"name": "Alice", "role": "user"})
    bob = store.create({"name": "Bob", "role": "user"})
    assert [r["id"] for r in store.read_all()] == [alice["id"], bob["id"]]

    store.update(alice["id"], {"role": "admin"})
    assert store.find_by_id(alice["id"])["role"] == "admin"
    assert store.find_by_id(bob["id"])["role"] == "user"

    store.delete(bob["id"])
    assert store.find_by_id(bob["id"]) is None
    assert [r["id"] for r in store.read_all()] == [alice["id"]]


def test_ids_stay_unique_after_delete_and_recreate(tmp_path):
    """레코드를 삭제한 뒤 새로 생성해도 id가 재사용되지 않아야 한다."""
    store = RecordStore(tmp_path / "db.json")

    first = store.create({"name": "Alice"})
    second = store.create({"name": "Bob"})
    store.delete(first["id"])

    third = store.create({"name": "Carol"})
    ids = [r["id"] for r in store.read_all()]

    assert len(ids) == len(set(ids))
    assert third["id"] != first["id"]
    assert third["id"] > second["id"]


def test_data_persists_across_repeated_restarts(tmp_path):
    """RecordStore를 여러 번 새로 생성(재시작)해도 누적된 데이터가 유지되어야 한다."""
    path = tmp_path / "db.json"

    RecordStore(path).create({"name": "Alice"})
    RecordStore(path).create({"name": "Bob"})
    third_session = RecordStore(path)
    third_session.update(1, {"role": "admin"})

    final_session = RecordStore(path)
    records = final_session.read_all()

    assert len(records) == 2
    assert records[0]["role"] == "admin"


def test_search_is_case_insensitive_partial_match(tmp_path):
    """키/값 검색의 대소문자 무시 부분일치 동작이 유지되어야 한다."""
    store = RecordStore(tmp_path / "db.json")
    store.create({"name": "Alice Kim"})
    store.create({"name": "Bob Lee"})

    results = store.search("name", "alice")
    assert len(results) == 1
    assert results[0]["name"] == "Alice Kim"


def test_unicode_data_roundtrips_through_file(tmp_path):
    """한글 등 유니코드 데이터가 저장/로드 과정에서 깨지지 않아야 한다."""
    path = tmp_path / "db.json"
    store = RecordStore(path)
    store.create({"name": "홍길동", "note": "특수문자 !@#$%^&*()"})

    reloaded = RecordStore(path).read_all()
    assert reloaded[0]["name"] == "홍길동"
    assert reloaded[0]["note"] == "특수문자 !@#$%^&*()"


def test_jsonlib_dumps_loads_roundtrip_matches_file_roundtrip(tmp_path):
    """문자열 기반(loads/dumps)과 파일 기반(load/save) 왕복 결과가 동일해야 한다."""
    data = {"a": 1, "b": ["x", "y"], "c": {"nested": True}}
    path = tmp_path / "db.json"

    jsonlib.save(data, path)
    from_file = jsonlib.load(path)
    from_string = jsonlib.loads(jsonlib.dumps(data))

    assert from_file == from_string == data
