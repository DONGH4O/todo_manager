"""Audit Todo Manager release artifact sizes for the M7.5 lightweight GUI work.

The release GUI is a one-file PyInstaller executable, so normal release tree
inspection can only see the outer ``todo-gui.exe``. When a PyInstaller workpath
is available, this script can also parse ``*.toc`` files to categorize the
archive internals before the build directory is removed.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BYTES_PER_MB = 1024 * 1024

ALLOWED_QTWEBENGINE_LOCALES = {"en-us", "zh-cn"}
QTWEBENGINE_LOCALE_RE = re.compile(
    r"(?:^|[\\/])(?:qtwebengine_)?locales[\\/](?P<tag>[a-z]{2}(?:[-_][a-z]{2})?)\.pak$",
    re.IGNORECASE,
)

DEVTOOLS_MARKERS = (
    "devtools",
    "qtwebengine_devtools",
)

UNUSED_QT_MODULE_MARKERS = (
    "qt3d",
    "qt6charts",
    "qtcharts",
    "qt6datavisualization",
    "qtdatavisualization",
    "qt6multimedia",
    "qtmultimedia",
    "qt6pdf",
    "qtpdf",
    "qt6quick3d",
    "qtquick3d",
)

FRONTEND_CACHE_MARKERS = (
    "/.next/",
    "/node_modules/",
    "/playwright-report/",
    "/test-results/",
)


@dataclass(frozen=True)
class SizeRecord:
    source: str
    path: str
    size: int
    kind: str = "file"


@dataclass(frozen=True)
class PolicyViolation:
    source: str
    path: str
    rule: str
    detail: str


def format_size(size: int) -> str:
    return f"{size / BYTES_PER_MB:.2f} MB"


def normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lower()


def qtwebengine_locale_tag(path: str | Path) -> str | None:
    match = QTWEBENGINE_LOCALE_RE.search(str(path).replace("\\", "/"))
    if not match:
        return None
    return match.group("tag").replace("_", "-").lower()


def classify_path(path: str | Path) -> str:
    normalized = normalize_path(path)
    name = normalized.rsplit("/", 1)[-1]

    if "desktop-react/" in normalized:
        return "react_desktop"
    if name in {"todo-gui.exe", "todo-gui"} or "todomanager.app/" in normalized:
        return "gui_binary"
    if name in {"todo.exe", "todo"}:
        return "cli_binary"
    if qtwebengine_locale_tag(normalized) is not None or "/translations/" in normalized:
        return "qt_locales"
    if "qtwebchannel" in normalized:
        return "qt_webchannel"
    if (
        "qtwebengine" in normalized
        or "qt6webengine" in normalized
        or "qtwebengineprocess" in normalized
        or "chromium" in normalized
        or "icudtl.dat" in normalized
        or "v8_context_snapshot" in normalized
    ):
        return "qt_webengine"
    if "/qml/" in normalized or "quick3d" in normalized:
        return "qt_qml_quick"
    if "pyside6" in normalized or name.startswith("qt6"):
        return "qt_runtime"
    if "base_library.zip" in normalized or "python" in normalized:
        return "python_runtime"
    if name in {"readme.txt", "install.bat", "todo-react.bat", "todo-react", "manifest.json"}:
        return "release_metadata"
    if Path(name).suffix.lower() in {".exe", ".dll", ".pyd", ".so", ".dylib"}:
        return "native_other"
    return "other"


def read_release_dir(release_dir: Path) -> list[SizeRecord]:
    if not release_dir.exists():
        raise FileNotFoundError(f"release directory is missing: {release_dir}")
    records: list[SizeRecord] = []
    for path in sorted(release_dir.rglob("*")):
        if path.is_file():
            records.append(
                SizeRecord(
                    source=f"release:{release_dir}",
                    path=path.relative_to(release_dir).as_posix(),
                    size=path.stat().st_size,
                )
            )
    return records


def read_zip(zip_path: Path) -> list[SizeRecord]:
    if not zip_path.exists():
        raise FileNotFoundError(f"zip is missing: {zip_path}")
    records: list[SizeRecord] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in sorted(zf.infolist(), key=lambda item: item.filename):
            if not info.is_dir():
                records.append(
                    SizeRecord(
                        source=f"zip:{zip_path}",
                        path=info.filename,
                        size=info.file_size,
                        kind="zip-entry",
                    )
                )
    return records


def _walk_toc_entries(value: Any) -> Iterable[tuple[str, str, str]]:
    if isinstance(value, (list, tuple)):
        if (
            len(value) >= 3
            and isinstance(value[0], str)
            and isinstance(value[1], str)
            and isinstance(value[2], str)
        ):
            yield (value[0], value[1], value[2])
            return
        for item in value:
            yield from _walk_toc_entries(item)


def _candidate_toc_files(workpath: Path) -> list[Path]:
    if workpath.is_file():
        return [workpath]
    for name in ("PKG-00.toc", "EXE-00.toc", "Analysis-00.toc"):
        preferred = sorted(workpath.rglob(name))
        if preferred:
            return preferred
    return sorted(workpath.rglob("*.toc"))


def read_pyinstaller_toc(workpath: Path) -> list[SizeRecord]:
    records: list[SizeRecord] = []
    seen: set[tuple[str, str, str, str]] = set()

    for toc_path in _candidate_toc_files(workpath):
        payload = ast.literal_eval(toc_path.read_text(encoding="utf-8", errors="replace"))
        for dest_name, source_path, typecode in _walk_toc_entries(payload):
            source = Path(source_path)
            size = source.stat().st_size if source.exists() and source.is_file() else 0
            record_key = (toc_path.as_posix(), dest_name, source_path, typecode)
            if record_key in seen:
                continue
            seen.add(record_key)
            records.append(
                SizeRecord(
                    source=f"toc:{toc_path}",
                    path=dest_name or source.name,
                    size=size,
                    kind=typecode,
                )
            )
    return records


def audit_pruning_policy(records: Iterable[SizeRecord]) -> list[PolicyViolation]:
    violations: list[PolicyViolation] = []
    for record in records:
        normalized = f"/{normalize_path(record.path)}/"
        tag = qtwebengine_locale_tag(record.path)
        if tag is not None and tag not in ALLOWED_QTWEBENGINE_LOCALES:
            violations.append(
                PolicyViolation(
                    source=record.source,
                    path=record.path,
                    rule="qtwebengine_locale",
                    detail=f"locale {tag} is outside the M7.5 allowlist",
                )
            )
        if any(marker in normalized for marker in DEVTOOLS_MARKERS):
            violations.append(
                PolicyViolation(
                    source=record.source,
                    path=record.path,
                    rule="qtwebengine_devtools",
                    detail="debug/devtools resource should not ship in release artifacts",
                )
            )
        if any(marker in normalized for marker in UNUSED_QT_MODULE_MARKERS):
            violations.append(
                PolicyViolation(
                    source=record.source,
                    path=record.path,
                    rule="unused_qt_module",
                    detail="unused Qt module is outside the React desktop shell runtime set",
                )
            )
        if any(marker in normalized for marker in FRONTEND_CACHE_MARKERS):
            violations.append(
                PolicyViolation(
                    source=record.source,
                    path=record.path,
                    rule="frontend_cache",
                    detail="frontend cache/test artifact should not ship in release artifacts",
                )
            )
    return sorted(violations, key=lambda item: (item.source, item.rule, item.path))


def summarize(records: list[SizeRecord]) -> dict[str, Any]:
    total = sum(record.size for record in records)
    categories: dict[str, int] = {}
    for record in records:
        category = classify_path(record.path)
        categories[category] = categories.get(category, 0) + record.size

    return {
        "total_bytes": total,
        "total_mb": round(total / BYTES_PER_MB, 2),
        "categories": [
            {
                "name": name,
                "bytes": size,
                "mb": round(size / BYTES_PER_MB, 2),
                "percent": round((size / total * 100), 2) if total else 0,
            }
            for name, size in sorted(categories.items(), key=lambda item: item[1], reverse=True)
        ],
        "top_files": [
            {
                "path": record.path,
                "bytes": record.size,
                "mb": round(record.size / BYTES_PER_MB, 2),
                "category": classify_path(record.path),
                "kind": record.kind,
            }
            for record in sorted(records, key=lambda item: item.size, reverse=True)[:20]
        ],
    }


def build_report(
    release_dir: Path | None,
    zip_path: Path | None,
    pyinstaller_workpath: Path | None,
) -> dict[str, Any]:
    inputs: list[dict[str, Any]] = []
    all_records: list[SizeRecord] = []

    for label, records in (
        ("release_dir", read_release_dir(release_dir) if release_dir else []),
        ("zip", read_zip(zip_path) if zip_path else []),
        (
            "pyinstaller_toc",
            read_pyinstaller_toc(pyinstaller_workpath) if pyinstaller_workpath else [],
        ),
    ):
        if records:
            all_records.extend(records)
            input_summary = summarize(records)
            input_summary["name"] = label
            input_summary["record_count"] = len(records)
            inputs.append(input_summary)

    violations = audit_pruning_policy(all_records)
    return {
        "schema": "todo-manager.release-size-audit.v1",
        "inputs": inputs,
        "policy": {
            "allowed_qtwebengine_locales": sorted(ALLOWED_QTWEBENGINE_LOCALES),
            "unused_qt_module_markers": sorted(UNUSED_QT_MODULE_MARKERS),
            "devtools_markers": sorted(DEVTOOLS_MARKERS),
        },
        "policy_violations": [
            {
                "source": violation.source,
                "path": violation.path,
                "rule": violation.rule,
                "detail": violation.detail,
            }
            for violation in violations
        ],
    }


def print_report(report: dict[str, Any]) -> None:
    for input_summary in report["inputs"]:
        print(
            f"[SIZE] {input_summary['name']}: "
            f"{input_summary['total_mb']:.2f} MB across {input_summary['record_count']} files"
        )
        for category in input_summary["categories"]:
            print(
                "  - "
                f"{category['name']}: {category['mb']:.2f} MB "
                f"({category['percent']:.2f}%)"
            )
        print("  Top files:")
        for record in input_summary["top_files"][:8]:
            print(
                "    "
                f"{record['mb']:.2f} MB  {record['category']}  {record['path']}"
            )

    violations = report["policy_violations"]
    if violations:
        print("[FAIL] M7.5 pruning policy violations:")
        for violation in violations:
            print(
                "  - "
                f"{violation['rule']}: {violation['path']} "
                f"({violation['detail']})"
            )
    else:
        print("[OK] M7.5 pruning policy check passed")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=Path("dist") / "TodoManager",
        help="Extracted release directory to audit.",
    )
    parser.add_argument(
        "--zip",
        dest="zip_path",
        type=Path,
        default=None,
        help="Optional release zip to audit.",
    )
    parser.add_argument(
        "--pyinstaller-workpath",
        type=Path,
        default=None,
        help="Optional PyInstaller workpath or .toc file for internal archive categories.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report output path.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of the human summary.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = build_report(args.release_dir, args.zip_path, args.pyinstaller_workpath)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_report(report)

    return 1 if report["policy_violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
