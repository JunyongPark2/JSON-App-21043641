import os
import tempfile
from pathlib import Path
from typing import Any, Union

from . import _json_impl

PathLike = Union[str, os.PathLike]


class JsonLibError(Exception):
    """jsonlib에서 발생하는 모든 예외의 기반 클래스"""


class JsonParseError(JsonLibError):
    """JSON 파싱(읽기) 중 발생하는 예외"""


class JsonSaveError(JsonLibError):
    """JSON 저장(쓰기) 중 발생하는 예외"""


def loads(text: str) -> Any:
    """JSON 문자열을 파이썬 객체로 파싱한다."""
    try:
        return _json_impl.parse(text)
    except _json_impl.JSONDecodeError as e:
        raise JsonParseError(f"JSON 문자열 파싱 실패: {e}") from e


def load(path: PathLike, encoding: str = "utf-8") -> Any:
    """JSON 파일을 읽어 파이썬 객체로 반환한다."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding=encoding)
    except FileNotFoundError as e:
        raise JsonParseError(f"파일을 찾을 수 없음: {file_path}") from e
    except OSError as e:
        raise JsonParseError(f"파일 읽기 실패: {file_path} ({e})") from e

    return loads(text)


def dumps(data: Any, *, indent: int = 2, ensure_ascii: bool = False) -> str:
    """파이썬 객체를 JSON 문자열로 직렬화한다."""
    try:
        return _json_impl.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    except TypeError as e:
        raise JsonSaveError(f"JSON 직렬화 실패: {e}") from e


def save(
    data: Any,
    path: PathLike,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    encoding: str = "utf-8",
) -> None:
    """파이썬 객체를 JSON 파일로 저장한다. 중간 경로가 없으면 생성하고,
    임시 파일에 먼저 쓴 뒤 원자적으로 교체하여 저장 중 오류로 인한
    파일 손상을 방지한다."""
    file_path = Path(path)
    text = dumps(data, indent=indent, ensure_ascii=ensure_ascii)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding=encoding) as f:
                f.write(text)
            os.replace(tmp_name, file_path)
        except BaseException:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
            raise
    except OSError as e:
        raise JsonSaveError(f"파일 저장 실패: {file_path} ({e})") from e
