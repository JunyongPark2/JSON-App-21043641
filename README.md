# JSON-App-21043641

JSON 파일을 데이터베이스처럼 사용하는 Python CRUD 콘솔 애플리케이션.

## 구성

```
JSON-App/
├── jsonlib/            # JSON 파싱/저장 라이브러리
│   ├── core.py          # load/save/loads/dumps, 예외 클래스
│   └── tests/
├── app/                 # CRUD 콘솔 애플리케이션
│   ├── storage.py        # RecordStore: jsonlib를 사용한 CRUD 저장소
│   ├── cli.py             # 메뉴 기반 콘솔 UI
│   └── tests/
├── data/db.json          # 실제 데이터 파일 (실행 시 자동 생성)
└── main.py               # 진입점
```

### jsonlib

JSON 파싱/저장을 담당하는 라이브러리.

- `load(path)` / `save(data, path)`: 파일 단위 읽기/쓰기
- `loads(text)` / `dumps(data)`: 문자열 단위 파싱/직렬화
- `JsonParseError` / `JsonSaveError`: 읽기/쓰기 실패 시 발생하는 예외
- `save()`는 임시 파일에 먼저 쓴 뒤 원자적으로 교체(`os.replace`)하여, 저장 도중 오류가 나도 기존 파일이 손상되지 않는다.

### app

`jsonlib`을 사용해 JSON 파일을 데이터베이스처럼 다루는 CRUD 계층.

- `RecordStore` (`app/storage.py`): 레코드 리스트에 대한 create/read/update/delete와 자동 증가 `id` 관리
- `cli.py`: 메뉴 기반 콘솔 UI (Create / Read / Update / Delete)

## 실행

```bash
python3 main.py
```

메뉴에서 번호를 선택해 사용한다.

- **Create**: `key=value` 형태로 필드를 한 줄씩 입력 (빈 줄 입력 시 종료)
- **Read**: 전체 목록 보기 / ID로 검색 / 키-값으로 검색
- **Update**: ID 선택 후 수정할 필드만 `key=value`로 입력 (`id`는 수정 불가)
- **Delete**: ID 선택 후 확인(`y`) 시에만 삭제

## 테스트

```bash
python3 -m pytest -q
```
