"""표준 json 모듈을 사용하지 않는 JSON 파서/직렬화기 구현.

RFC 8259 문법을 기반으로 한 손수 작성한 재귀 하강 파서(parse)와
직렬화기(dumps)를 제공한다.
"""

from typing import Any

_WHITESPACE = " \t\n\r"
_DIGITS = "0123456789"

_ESCAPE_TO_CHAR = {
    '"': '"',
    "\\": "\\",
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}

_CHAR_TO_ESCAPE = {
    '"': '\\"',
    "\\": "\\\\",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


class JSONDecodeError(ValueError):
    """JSON 문자열 파싱 실패 시 발생하는 예외 (위치 정보 포함)."""

    def __init__(self, msg: str, doc: str, pos: int):
        lineno = doc.count("\n", 0, pos) + 1
        colno = pos - doc.rfind("\n", 0, pos)
        message = f"{msg}: line {lineno} column {colno} (char {pos})"
        super().__init__(message)
        self.msg = msg
        self.doc = doc
        self.pos = pos
        self.lineno = lineno
        self.colno = colno


def parse(text: str) -> Any:
    """JSON 문자열을 파이썬 객체로 파싱한다."""
    if not isinstance(text, str):
        raise TypeError(f"the JSON object must be str, not {type(text).__name__}")

    pos = _skip_ws(text, 0)
    value, pos = _parse_value(text, pos)
    pos = _skip_ws(text, pos)
    if pos != len(text):
        raise JSONDecodeError("Extra data", text, pos)
    return value


def dumps(obj: Any, *, indent: int = None, ensure_ascii: bool = True) -> str:
    """파이썬 객체를 JSON 문자열로 직렬화한다."""
    buf: list = []
    _write_value(obj, buf, indent, ensure_ascii, 0)
    return "".join(buf)


# ---------------------------------------------------------------------------
# 파싱
# ---------------------------------------------------------------------------

def _skip_ws(s: str, i: int) -> int:
    n = len(s)
    while i < n and s[i] in _WHITESPACE:
        i += 1
    return i


def _parse_value(s: str, i: int):
    n = len(s)
    if i >= n:
        raise JSONDecodeError("Expecting value", s, i)

    ch = s[i]
    if ch == "{":
        return _parse_object(s, i)
    if ch == "[":
        return _parse_array(s, i)
    if ch == '"':
        return _parse_string(s, i)
    if s.startswith("true", i):
        return True, i + 4
    if s.startswith("false", i):
        return False, i + 5
    if s.startswith("null", i):
        return None, i + 4
    if ch == "-" or ch in _DIGITS:
        return _parse_number(s, i)

    raise JSONDecodeError("Expecting value", s, i)


def _parse_object(s: str, i: int):
    obj = {}
    i = _skip_ws(s, i + 1)  # '{' 건너뛰기
    n = len(s)

    if i < n and s[i] == "}":
        return obj, i + 1

    while True:
        i = _skip_ws(s, i)
        if i >= n or s[i] != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, i
            )
        key, i = _parse_string(s, i)

        i = _skip_ws(s, i)
        if i >= n or s[i] != ":":
            raise JSONDecodeError("Expecting ':' delimiter", s, i)
        i = _skip_ws(s, i + 1)

        value, i = _parse_value(s, i)
        obj[key] = value

        i = _skip_ws(s, i)
        if i >= n:
            raise JSONDecodeError("Expecting ',' delimiter", s, i)
        if s[i] == ",":
            i += 1
            continue
        if s[i] == "}":
            return obj, i + 1
        raise JSONDecodeError("Expecting ',' delimiter", s, i)


def _parse_array(s: str, i: int):
    arr = []
    i = _skip_ws(s, i + 1)  # '[' 건너뛰기
    n = len(s)

    if i < n and s[i] == "]":
        return arr, i + 1

    while True:
        i = _skip_ws(s, i)
        value, i = _parse_value(s, i)
        arr.append(value)

        i = _skip_ws(s, i)
        if i >= n:
            raise JSONDecodeError("Expecting ',' delimiter", s, i)
        if s[i] == ",":
            i += 1
            continue
        if s[i] == "]":
            return arr, i + 1
        raise JSONDecodeError("Expecting ',' delimiter", s, i)


def _parse_string(s: str, i: int):
    start_quote = i
    i += 1  # 여는 큰따옴표 건너뛰기
    n = len(s)
    chunk_start = i
    chunks = []

    while True:
        if i >= n:
            raise JSONDecodeError("Unterminated string starting at", s, start_quote)

        ch = s[i]
        if ch == '"':
            chunks.append(s[chunk_start:i])
            return "".join(chunks), i + 1

        if ch == "\\":
            chunks.append(s[chunk_start:i])
            i += 1
            if i >= n:
                raise JSONDecodeError(
                    "Unterminated string starting at", s, start_quote
                )
            esc = s[i]
            if esc == "u":
                codepoint, i = _parse_unicode_escape(s, i)
                if 0xD800 <= codepoint <= 0xDBFF and s[i : i + 2] == "\\u":
                    low, next_i = _parse_unicode_escape(s, i + 1)
                    if 0xDC00 <= low <= 0xDFFF:
                        codepoint = 0x10000 + ((codepoint - 0xD800) << 10) + (
                            low - 0xDC00
                        )
                        i = next_i
                chunks.append(chr(codepoint))
                chunk_start = i
                continue
            if esc in _ESCAPE_TO_CHAR:
                chunks.append(_ESCAPE_TO_CHAR[esc])
                i += 1
                chunk_start = i
                continue
            raise JSONDecodeError(f"Invalid \\escape: {esc!r}", s, i)

        if ord(ch) < 0x20:
            raise JSONDecodeError("Invalid control character", s, i)

        i += 1


def _parse_unicode_escape(s: str, i: int):
    """s[i] == 'u' 인 위치에서 시작하는 \\uXXXX 4자리 hex를 파싱한다."""
    hex_digits = s[i + 1 : i + 5]
    if len(hex_digits) != 4:
        raise JSONDecodeError("Invalid \\uXXXX escape", s, i)
    try:
        codepoint = int(hex_digits, 16)
    except ValueError:
        raise JSONDecodeError("Invalid \\uXXXX escape", s, i) from None
    return codepoint, i + 5


def _parse_number(s: str, i: int):
    n = len(s)
    start = i

    if s[i] == "-":
        i += 1
        if i >= n or s[i] not in _DIGITS:
            raise JSONDecodeError("Expecting value", s, start)

    if s[i] == "0":
        i += 1
    else:
        while i < n and s[i] in _DIGITS:
            i += 1

    is_float = False

    if i < n and s[i] == ".":
        is_float = True
        i += 1
        if i >= n or s[i] not in _DIGITS:
            raise JSONDecodeError("Expecting value", s, start)
        while i < n and s[i] in _DIGITS:
            i += 1

    if i < n and s[i] in "eE":
        is_float = True
        i += 1
        if i < n and s[i] in "+-":
            i += 1
        if i >= n or s[i] not in _DIGITS:
            raise JSONDecodeError("Expecting value", s, start)
        while i < n and s[i] in _DIGITS:
            i += 1

    literal = s[start:i]
    return (float(literal) if is_float else int(literal)), i


# ---------------------------------------------------------------------------
# 직렬화
# ---------------------------------------------------------------------------

def _write_value(obj: Any, buf: list, indent, ensure_ascii: bool, level: int) -> None:
    if obj is None:
        buf.append("null")
    elif obj is True:
        buf.append("true")
    elif obj is False:
        buf.append("false")
    elif isinstance(obj, str):
        buf.append(_encode_string(obj, ensure_ascii))
    elif isinstance(obj, int):
        buf.append(str(obj))
    elif isinstance(obj, float):
        buf.append(_encode_float(obj))
    elif isinstance(obj, dict):
        _write_object(obj, buf, indent, ensure_ascii, level)
    elif isinstance(obj, (list, tuple)):
        _write_array(obj, buf, indent, ensure_ascii, level)
    else:
        raise TypeError(
            f"Object of type {type(obj).__name__} is not JSON serializable"
        )


def _encode_float(value: float) -> str:
    if value != value:  # NaN
        return "NaN"
    if value == float("inf"):
        return "Infinity"
    if value == float("-inf"):
        return "-Infinity"
    return repr(value)


def _encode_string(s: str, ensure_ascii: bool) -> str:
    out = ['"']
    for ch in s:
        if ch in _CHAR_TO_ESCAPE:
            out.append(_CHAR_TO_ESCAPE[ch])
        elif ord(ch) < 0x20:
            out.append(f"\\u{ord(ch):04x}")
        elif ensure_ascii and ord(ch) > 0x7E:
            codepoint = ord(ch)
            if codepoint > 0xFFFF:
                codepoint -= 0x10000
                hi = 0xD800 + (codepoint >> 10)
                lo = 0xDC00 + (codepoint & 0x3FF)
                out.append(f"\\u{hi:04x}\\u{lo:04x}")
            else:
                out.append(f"\\u{codepoint:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _indent_strs(indent, level):
    if indent is None:
        return "", "", ""
    newline = "\n"
    pad = " " * (indent * (level + 1))
    pad_close = " " * (indent * level)
    return newline, pad, pad_close


def _write_object(obj: dict, buf: list, indent, ensure_ascii: bool, level: int) -> None:
    if not obj:
        buf.append("{}")
        return

    newline, pad, pad_close = _indent_strs(indent, level)
    buf.append("{")
    items = list(obj.items())
    for idx, (key, value) in enumerate(items):
        if not isinstance(key, str):
            raise TypeError(
                f"keys must be str, not {type(key).__name__}"
            )
        buf.append(newline)
        buf.append(pad)
        buf.append(_encode_string(key, ensure_ascii))
        buf.append(": " if indent is not None else ":")
        _write_value(value, buf, indent, ensure_ascii, level + 1)
        if idx != len(items) - 1:
            buf.append(",")
    buf.append(newline)
    buf.append(pad_close)
    buf.append("}")


def _write_array(arr, buf: list, indent, ensure_ascii: bool, level: int) -> None:
    if not arr:
        buf.append("[]")
        return

    newline, pad, pad_close = _indent_strs(indent, level)
    buf.append("[")
    for idx, value in enumerate(arr):
        buf.append(newline)
        buf.append(pad)
        _write_value(value, buf, indent, ensure_ascii, level + 1)
        if idx != len(arr) - 1:
            buf.append(",")
    buf.append(newline)
    buf.append(pad_close)
    buf.append("]")
