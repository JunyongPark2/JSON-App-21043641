"""JSON 파일을 데이터베이스처럼 사용하는 저장소 계층.

jsonlib(load/save)로 파일 입출력을 위임하고, 레코드 리스트에 대한
CRUD 연산을 제공한다.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonlib

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "db.json"


class RecordStore:
    def __init__(self, path: Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        self._records: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        data = jsonlib.load(self.path)
        if not isinstance(data, list):
            raise jsonlib.JsonLibError(
                f"{self.path}의 데이터 형식이 리스트가 아닙니다."
            )
        return data

    def _save(self) -> None:
        jsonlib.save(self._records, self.path)

    def _next_id(self) -> int:
        if not self._records:
            return 1
        return max(r.get("id", 0) for r in self._records) + 1

    # ---- Create ----
    def create(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        record = {"id": self._next_id(), **fields}
        self._records.append(record)
        self._save()
        return record

    # ---- Read ----
    def read_all(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def find_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        return next((r for r in self._records if r.get("id") == record_id), None)

    def search(self, key: str, value: str) -> List[Dict[str, Any]]:
        needle = str(value).lower()
        return [
            r for r in self._records
            if needle in str(r.get(key, "")).lower()
        ]

    # ---- Update ----
    def update(self, record_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        record = self.find_by_id(record_id)
        if record is None:
            return None
        record.update(updates)
        self._save()
        return record

    # ---- Delete ----
    def delete(self, record_id: int) -> bool:
        record = self.find_by_id(record_id)
        if record is None:
            return False
        self._records.remove(record)
        self._save()
        return True
