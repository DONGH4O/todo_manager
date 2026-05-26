"""React desktop shell backed by PySide6 QtWebEngine."""

from __future__ import annotations

import json
import locale
import os
import sys
from pathlib import Path
from typing import Any

QTWEBENGINE_SOFTWARE_RENDER_FLAGS = (
    "--disable-gpu",
    "--disable-gpu-compositing",
    "--disable-gpu-rasterization",
    "--disable-zero-copy",
    "--disable-accelerated-2d-canvas",
)


def _flag_name(flag: str) -> str:
    return flag.split("=", 1)[0]


def _merge_chromium_flags(current: str, extra_flags: tuple[str, ...]) -> str:
    flags = current.split()
    existing = {_flag_name(flag) for flag in flags}
    for flag in extra_flags:
        if _flag_name(flag) not in existing:
            flags.append(flag)
    return " ".join(flags)


def _configure_qtwebengine_rendering() -> None:
    mode = os.environ.get("TODO_MANAGER_QTWEBENGINE_RENDERING", "software").strip().lower()
    if mode in {"hardware", "gpu", "default"}:
        return

    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = _merge_chromium_flags(
        os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", ""),
        QTWEBENGINE_SOFTWARE_RENDER_FLAGS,
    )
    os.environ.setdefault("QT_OPENGL", "software")


_configure_qtwebengine_rendering()

from todo_manager.engine.storage import DataFileError, DataWriteError, set_data_dir
from todo_manager.engine.task_manager import (
    create_subtask,
    create_task,
    delete_task,
    get_task,
    get_tasks_for_dates,
    list_all_tasks,
    undo_task,
    update_subtask,
    update_task,
)
from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

from todo_manager.gui.icon import apply_app_icon


ROOT = Path(__file__).resolve().parent.parent
VALID_ACTIONS = {
    "listTasks",
    "listTasksForDates",
    "createTask",
    "updateTask",
    "deleteTask",
    "undoTask",
    "createSubtask",
    "updateSubtask",
}


def _response(ok: bool, payload: Any) -> str:
    if ok:
        return json.dumps({"ok": True, "result": payload}, ensure_ascii=False)
    return json.dumps({"ok": False, "error": payload}, ensure_ascii=False)


def _error(code: str, message: str, **details: Any) -> str:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return _response(False, error)


def _object_payload(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return value
    return dict(value)


def _not_found(message: str) -> str:
    return _error("not_found", message)


def _validation_error(exc: ValueError) -> str:
    message = str(exc)
    if "不存在" in message or "未找到" in message:
        return _not_found(message)
    return _error("validation_error", message)


def _decode_cli_stream(data: bytes) -> str:
    """Decode CLI output from source Python or frozen Windows executables."""
    preferred_encodings = ["utf-8", locale.getpreferredencoding(False)]
    if sys.platform.startswith("win"):
        preferred_encodings.append("mbcs")

    seen: set[str] = set()
    for encoding in preferred_encodings:
        normalized = encoding.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        try:
            return data.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue

    return data.decode("utf-8", errors="replace")


def _collect_update(payload: dict[str, Any]) -> dict[str, Any]:
    update: dict[str, Any] = {}
    for field in ("title", "start_date", "end_date", "status", "background"):
        value = payload.get(field)
        if isinstance(value, str):
            update[field] = value
    return update


class TodoBridge(QObject):
    def __init__(self, data_dir: str | None):
        super().__init__()
        self.data_dir = data_dir

    @Slot(str, result=str)
    def request(self, raw_request: str) -> str:
        try:
            request = json.loads(raw_request)
            if not isinstance(request, dict):
                return _error("bridge_request_error", "Bridge request must be an object")
            action = str(request.get("action") or "")
            if action not in VALID_ACTIONS:
                return _error("bridge_request_error", f"Unsupported todo bridge action: {action}")
            payload = request.get("payload")
            if not isinstance(payload, dict):
                payload = {}
        except Exception as exc:
            return _error("bridge_request_error", str(exc))

        try:
            if self.data_dir:
                set_data_dir(self.data_dir)

            if action == "listTasks":
                return _response(True, [_object_payload(task) for task in list_all_tasks()])

            if action == "listTasksForDates":
                dates = payload.get("dates")
                if not isinstance(dates, list):
                    return _error("validation_error", "dates must be a list")
                date_strs = [str(item) for item in dates if isinstance(item, str)]
                tasks_by_date = get_tasks_for_dates(date_strs)
                return _response(
                    True,
                    {
                        date_str: [_object_payload(task) for task in tasks]
                        for date_str, tasks in tasks_by_date.items()
                    },
                )

            if action == "createTask":
                task = create_task(
                    str(payload.get("title") or ""),
                    str(payload.get("start_date") or ""),
                    str(payload.get("end_date") or ""),
                    str(payload.get("status") or ""),
                    str(payload.get("background") or ""),
                )
                return _response(True, _object_payload(task))

            if action == "updateTask":
                update = payload.get("update")
                task = update_task(str(payload.get("taskId") or ""), **_collect_update(update if isinstance(update, dict) else {}))
                return _response(True, _object_payload(task))

            if action == "deleteTask":
                task_id = str(payload.get("taskId") or "")
                current = get_task(task_id)
                if current is None:
                    return _not_found(f"未找到任务: {task_id}")
                if not current.deleted and not delete_task(task_id):
                    return _error("internal_error", f"删除失败: {task_id}")
                return _response(True, _object_payload(get_task(task_id) or current))

            if action == "undoTask":
                task_id = str(payload.get("taskId") or "")
                current = get_task(task_id)
                if current is None:
                    return _not_found(f"未找到任务: {task_id}")
                if current.deleted and not undo_task(task_id):
                    return _error("internal_error", f"撤销删除失败: {task_id}")
                return _response(True, _object_payload(get_task(task_id) or current))

            if action == "createSubtask":
                input_payload = payload.get("input")
                if not isinstance(input_payload, dict):
                    input_payload = {}
                subtask = create_subtask(
                    str(payload.get("taskId") or ""),
                    str(input_payload.get("title") or ""),
                    str(input_payload.get("start_date") or ""),
                    str(input_payload.get("end_date") or ""),
                    str(input_payload.get("status") or ""),
                    str(input_payload.get("background") or ""),
                )
                return _response(True, _object_payload(subtask))

            if action == "updateSubtask":
                update = payload.get("update")
                subtask = update_subtask(
                    str(payload.get("taskId") or ""),
                    str(payload.get("subtaskId") or ""),
                    **_collect_update(update if isinstance(update, dict) else {}),
                )
                return _response(True, _object_payload(subtask))
        except ValueError as exc:
            return _validation_error(exc)
        except (DataFileError, DataWriteError) as exc:
            return _error("data_file_error", str(exc))
        except Exception as exc:
            return _error("internal_error", str(exc))

        return _error("bridge_request_error", f"Unsupported todo bridge action: {action}")


def _resolve_index_html(react_root: str | None = None) -> Path:
    if react_root:
        candidate = Path(react_root).expanduser().resolve()
        if candidate.is_dir():
            candidate = candidate / "index.html"
        return candidate

    app_dir = Path(sys.executable).resolve().parent
    release_index = app_dir / "desktop-react" / "ui" / "index.html"
    if release_index.exists():
        return release_index
    return ROOT / "frontend" / "out" / "index.html"


def _install_desktop_shell_script(view: QWebEngineView) -> None:
    script = QWebEngineScript()
    script.setName("TodoManagerDesktopShellMarker")
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(False)
    script.setSourceCode(
        """
(function () {
  window.todoDesktopShell = true;
  if (document.documentElement) {
    document.documentElement.dataset.desktopShell = "true";
  }
})();
"""
    )
    view.page().scripts().insert(script)


def _install_bridge_script(view: QWebEngineView) -> None:
    script = QWebEngineScript()
    script.setName("TodoManagerDesktopBridge")
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setRunsOnSubFrames(False)
    script.setSourceCode(
        """
(function () {
  window.todoDesktopShell = true;

  function installBridge() {
    if (window.todoBridge) return;
    if (typeof QWebChannel === "undefined" || !window.qt || !qt.webChannelTransport) {
      window.dispatchEvent(new Event("todoBridgeUnavailable"));
      return;
    }

    new QWebChannel(qt.webChannelTransport, function (channel) {
      var backend = channel.objects.todoBridgeBackend;
      window.todoBridge = {
        request: function (request) {
          return new Promise(function (resolve) {
            backend.request(JSON.stringify(request), function (response) {
              resolve(JSON.parse(response));
            });
          });
        }
      };
      window.dispatchEvent(new Event("todoBridgeReady"));
    });
  }

  if (typeof QWebChannel !== "undefined") {
    installBridge();
    return;
  }

  var script = document.createElement("script");
  script.src = "qrc:///qtwebchannel/qwebchannel.js";
  script.onload = installBridge;
  script.onerror = function () {
    window.dispatchEvent(new Event("todoBridgeUnavailable"));
  };

  var target = document.head || document.body || document.documentElement;
  if (target) {
    target.appendChild(script);
  } else {
    window.dispatchEvent(new Event("todoBridgeUnavailable"));
  }
})();
"""
    )
    view.page().scripts().insert(script)


def run_react_app(data_dir: str | None = None, react_root: str | None = None) -> int:
    index_html = _resolve_index_html(react_root)
    if not index_html.exists():
        print(f"React desktop bundle not found: {index_html}", file=sys.stderr)
        return 2

    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("Todo Manager")
    app.setOrganizationName("WorkBuddy")
    apply_app_icon(app)
    view = QWebEngineView()
    view.setWindowTitle("Todo Manager")
    apply_app_icon(app, view)
    view.resize(1366, 820)
    view.setMinimumSize(390, 720)

    bridge = TodoBridge(data_dir=data_dir)
    channel = QWebChannel(view.page())
    channel.registerObject("todoBridgeBackend", bridge)
    view.page().setWebChannel(channel)
    view._todo_bridge = bridge
    view._todo_channel = channel

    _install_desktop_shell_script(view)
    _install_bridge_script(view)
    url = QUrl.fromLocalFile(str(index_html))
    url.setQuery("desktop=1")
    view.load(url)
    view.show()
    return app.exec()
