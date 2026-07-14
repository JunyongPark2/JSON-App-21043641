"""JSON 파일 기반 CRUD 콘솔 애플리케이션."""

from typing import Dict

import jsonlib
from app.storage import RecordStore


def prompt_fields() -> Dict[str, str]:
    """'키=값' 형태를 한 줄씩 입력받아 dict로 변환한다. 빈 줄 입력 시 종료."""
    fields: Dict[str, str] = {}
    print("필드를 'key=value' 형태로 입력하세요. (입력을 마치려면 빈 줄 입력)")
    while True:
        line = input("  > ").strip()
        if not line:
            break
        if "=" not in line:
            print("  형식이 올바르지 않습니다. 'key=value' 형태로 입력하세요.")
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            print("  key는 비어 있을 수 없습니다.")
            continue
        fields[key] = value
    return fields


def prompt_id(message: str = "ID를 입력하세요: "):
    raw = input(message).strip()
    try:
        return int(raw)
    except ValueError:
        print("숫자로 된 ID를 입력해야 합니다.")
        return None


def print_record(record: dict) -> None:
    print(jsonlib.dumps(record))


def print_records(records: list) -> None:
    if not records:
        print("(데이터 없음)")
        return
    for record in records:
        print_record(record)


def do_create(store: RecordStore) -> None:
    print("[Create] 새 데이터를 입력합니다.")
    fields = prompt_fields()
    if not fields:
        print("입력된 필드가 없어 취소합니다.")
        return
    record = store.create(fields)
    print("생성 완료:")
    print_record(record)


def do_read(store: RecordStore) -> None:
    print("[Read] 1) 전체 목록  2) ID로 검색  3) 키/값으로 검색")
    choice = input("선택: ").strip()
    if choice == "1":
        print_records(store.read_all())
    elif choice == "2":
        record_id = prompt_id()
        if record_id is None:
            return
        record = store.find_by_id(record_id)
        if record is None:
            print(f"ID {record_id}에 해당하는 데이터가 없습니다.")
        else:
            print_record(record)
    elif choice == "3":
        key = input("검색할 키 이름: ").strip()
        value = input("검색할 값: ").strip()
        if not key:
            print("키 이름은 비어 있을 수 없습니다.")
            return
        print_records(store.search(key, value))
    else:
        print("잘못된 선택입니다.")


def do_update(store: RecordStore) -> None:
    print("[Update] 수정할 데이터를 선택합니다.")
    record_id = prompt_id()
    if record_id is None:
        return
    record = store.find_by_id(record_id)
    if record is None:
        print(f"ID {record_id}에 해당하는 데이터가 없습니다.")
        return

    print("현재 데이터:")
    print_record(record)
    print("수정할 필드를 입력하세요. (id는 수정할 수 없습니다)")
    updates = prompt_fields()
    updates.pop("id", None)
    if not updates:
        print("수정할 필드가 없어 취소합니다.")
        return

    updated = store.update(record_id, updates)
    print("수정 완료:")
    print_record(updated)


def do_delete(store: RecordStore) -> None:
    print("[Delete] 삭제할 데이터를 선택합니다.")
    record_id = prompt_id()
    if record_id is None:
        return
    record = store.find_by_id(record_id)
    if record is None:
        print(f"ID {record_id}에 해당하는 데이터가 없습니다.")
        return

    print("삭제 대상:")
    print_record(record)
    confirm = input("정말 삭제하시겠습니까? (y/N): ").strip().lower()
    if confirm != "y":
        print("삭제를 취소했습니다.")
        return

    store.delete(record_id)
    print(f"ID {record_id} 데이터를 삭제했습니다.")


MENU = """
==== JSON CRUD 콘솔 애플리케이션 ====
1. Create - 새 데이터 추가
2. Read   - 데이터 조회
3. Update - 데이터 수정
4. Delete - 데이터 삭제
0. 종료
"""

ACTIONS = {
    "1": do_create,
    "2": do_read,
    "3": do_update,
    "4": do_delete,
}


def run(store: RecordStore = None) -> None:
    store = store or RecordStore()
    while True:
        print(MENU)
        choice = input("메뉴를 선택하세요: ").strip()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        action = ACTIONS.get(choice)
        if action is None:
            print("잘못된 메뉴입니다. 다시 선택해주세요.")
            continue

        try:
            action(store)
        except jsonlib.JsonLibError as e:
            print(f"오류가 발생했습니다: {e}")


if __name__ == "__main__":
    run()
