from app.storage import RecordStore


def test_create_assigns_incrementing_ids(tmp_path):
    store = RecordStore(tmp_path / "db.json")

    first = store.create({"name": "Alice"})
    second = store.create({"name": "Bob"})

    assert first["id"] == 1
    assert second["id"] == 2
    assert [r["name"] for r in store.read_all()] == ["Alice", "Bob"]


def test_persists_across_instances(tmp_path):
    path = tmp_path / "db.json"
    RecordStore(path).create({"name": "Alice"})

    reloaded = RecordStore(path)
    assert len(reloaded.read_all()) == 1
    assert reloaded.read_all()[0]["name"] == "Alice"


def test_find_by_id(tmp_path):
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})

    assert store.find_by_id(record["id"])["name"] == "Alice"
    assert store.find_by_id(999) is None


def test_search_by_key_value(tmp_path):
    store = RecordStore(tmp_path / "db.json")
    store.create({"name": "Alice", "role": "admin"})
    store.create({"name": "Bob", "role": "user"})

    results = store.search("role", "admin")
    assert len(results) == 1
    assert results[0]["name"] == "Alice"


def test_update_modifies_fields(tmp_path):
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice", "role": "user"})

    updated = store.update(record["id"], {"role": "admin"})
    assert updated["role"] == "admin"
    assert store.find_by_id(record["id"])["role"] == "admin"


def test_update_missing_id_returns_none(tmp_path):
    store = RecordStore(tmp_path / "db.json")
    assert store.update(999, {"role": "admin"}) is None


def test_delete_removes_record(tmp_path):
    store = RecordStore(tmp_path / "db.json")
    record = store.create({"name": "Alice"})

    assert store.delete(record["id"]) is True
    assert store.find_by_id(record["id"]) is None
    assert store.delete(record["id"]) is False
