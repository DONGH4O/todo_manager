"""CLI agent contract helpers: JSON envelopes, error codes, exit codes."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO


EXIT_SUCCESS = 0
EXIT_USAGE = 2
EXIT_VALIDATION = 3
EXIT_NOT_FOUND = 4
EXIT_DATA_FILE = 5
EXIT_INTERNAL = 6
EXIT_INTERRUPTED = 130


_JSON_MODE = False


class CliExit(SystemExit):
    """SystemExit carrying a structured CLI error code."""

    def __init__(self, exit_code: int, error_code: str, message: str):
        super().__init__(exit_code)
        self.exit_code = exit_code
        self.error_code = error_code
        self.message = message


def set_json_mode(enabled: bool) -> None:
    global _JSON_MODE
    _JSON_MODE = bool(enabled)


def is_json_mode(args: Any | None = None) -> bool:
    return bool(getattr(args, "json", False)) or _JSON_MODE


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return str(value)


def write_json(payload: dict[str, Any], stream: TextIO) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=_json_default), file=stream)


def emit_success(args: Any, command: str, result: dict[str, Any]) -> bool:
    """Emit a success envelope in JSON mode.

    Returns True when JSON was emitted so callers can skip text output.
    """
    if not is_json_mode(args):
        return False
    write_json({"ok": True, "command": command, "result": result}, sys.stdout)
    return True


def error_payload(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"ok": False, "error": error}


def emit_error(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
) -> None:
    write_json(error_payload(code, message, details=details), sys.stderr)


def fail(
    message: str,
    *,
    error_code: str = "validation_error",
    exit_code: int = EXIT_VALIDATION,
    details: dict[str, Any] | None = None,
) -> None:
    if is_json_mode():
        emit_error(error_code, message, details=details)
    else:
        print(f"错误: {message}", file=sys.stderr)
    raise CliExit(exit_code, error_code, message)


def fail_for_value_error(exc: ValueError) -> None:
    message = str(exc)
    if "不存在" in message or "未找到" in message:
        fail(message, error_code="not_found", exit_code=EXIT_NOT_FOUND)
    fail(message, error_code="validation_error", exit_code=EXIT_VALIDATION)
