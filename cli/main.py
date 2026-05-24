"""D2 CLI 入口：argparse 参数解析与命令分发。

用法：
  python -m todo_manager.cli <command> [args...]
  todo <command> [args...]          # 安装后
"""

import argparse
import sys

from todo_manager.engine.storage import StorageError, clear_data_dir, set_data_dir
from todo_manager.cli.contract import (
    CliExit,
    EXIT_DATA_FILE,
    EXIT_INTERNAL,
    EXIT_INTERRUPTED,
    EXIT_SUCCESS,
    EXIT_USAGE,
    emit_error,
    is_json_mode,
    set_json_mode,
)
from todo_manager.cli.commands import (
    cmd_add, cmd_list, cmd_show, cmd_edit, cmd_delete, cmd_undo,
    cmd_sub_add, cmd_sub_list, cmd_sub_show, cmd_sub_edit,
    cmd_sub_delete, cmd_sub_undo,
    cmd_cal, cmd_search, cmd_stats,
)


class _GlobalOptionError(ValueError):
    pass


class TodoArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if is_json_mode():
            emit_error("usage_error", message)
            raise SystemExit(EXIT_USAGE)
        super().error(message)


def _extract_global_options(argv: list[str]) -> tuple[list[str], str | None, bool]:
    """Allow --json and --data-dir before or after subcommands."""
    json_mode = False
    data_dir = None
    remaining: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--json":
            json_mode = True
            i += 1
            continue
        if token == "--data-dir":
            if i + 1 >= len(argv):
                raise _GlobalOptionError("argument --data-dir: expected one argument")
            data_dir = argv[i + 1]
            i += 2
            continue
        if token.startswith("--data-dir="):
            data_dir = token.split("=", 1)[1]
            i += 1
            continue
        remaining.append(token)
        i += 1
    return remaining, data_dir, json_mode


def _build_parser() -> argparse.ArgumentParser:
    parser = TodoArgumentParser(
        prog="todo",
        description="命令行待办事项管理器",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="指定数据目录（默认开发态为项目 data，打包后为系统应用数据目录）",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="以稳定 JSON envelope 输出结果；错误 JSON 输出到 stderr",
    )

    sub = parser.add_subparsers(dest="command", title="命令")

    # ── todo add ────────────────────────────────────────
    p_add = sub.add_parser("add", help="新建任务")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument("-s", "--start", help="开始日期 (YYYY-MM-DD)，默认今天")
    p_add.add_argument("-e", "--end", help="截止日期 (YYYY-MM-DD)，默认今天")
    p_add.add_argument("--status", help=f"状态: 未启动|完成中|已完成|已取消，默认未启动")
    p_add.add_argument("-b", "--background", help="任务背景及目标（≤500字）")
    p_add.set_defaults(func=cmd_add)

    # ── todo list ───────────────────────────────────────
    p_list = sub.add_parser("list", help="列出任务")
    p_list.add_argument("-d", "--date", help="按日期筛选 (YYYY-MM-DD)")
    p_list.add_argument("--deleted", action="store_true", help="含已删除任务")
    p_list.set_defaults(func=cmd_list)

    # ── todo show ───────────────────────────────────────
    p_show = sub.add_parser("show", help="查看任务详情")
    p_show.add_argument("task_id", help="任务 ID")
    p_show.add_argument("--history", type=int, default=5, choices=range(1, 51),
                        metavar="N", help="历史记录条数 (1-50，默认 5)")
    p_show.set_defaults(func=cmd_show)

    # ── todo edit ───────────────────────────────────────
    p_edit = sub.add_parser("edit", help="编辑任务")
    p_edit.add_argument("task_id", help="任务 ID")
    p_edit.add_argument("-t", "--title", help="新标题")
    p_edit.add_argument("-s", "--start", help="新开始日期")
    p_edit.add_argument("-e", "--end", help="新截止日期")
    p_edit.add_argument("--status", help="新状态")
    p_edit.add_argument("-b", "--background", help="新背景描述")
    p_edit.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_edit.set_defaults(func=cmd_edit)

    # ── todo delete ─────────────────────────────────────
    p_delete = sub.add_parser("delete", help="删除任务")
    p_delete.add_argument("task_id", help="任务 ID")
    p_delete.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_delete.set_defaults(func=cmd_delete)

    # ── todo undo ───────────────────────────────────────
    p_undo = sub.add_parser("undo", help="撤销删除")
    p_undo.add_argument("task_id", help="任务 ID")
    p_undo.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_undo.set_defaults(func=cmd_undo)

    # ── todo sub ────────────────────────────────────────
    p_sub = sub.add_parser("sub", help="子任务操作")
    sub_sub = p_sub.add_subparsers(dest="sub_command", title="子任务命令")

    # sub add
    p_sub_add = sub_sub.add_parser("add", help="新建子任务")
    p_sub_add.add_argument("task_id", help="父任务 ID")
    p_sub_add.add_argument("title", help="子任务标题")
    p_sub_add.add_argument("-s", "--start", help="开始日期")
    p_sub_add.add_argument("-e", "--end", help="截止日期")
    p_sub_add.add_argument("--status", help="状态: 未启动|完成中|已完成|已取消，默认未启动")
    p_sub_add.add_argument("-b", "--background", help="背景描述")
    p_sub_add.set_defaults(func=cmd_sub_add)

    # sub list
    p_sub_list = sub_sub.add_parser("list", help="列出子任务")
    p_sub_list.add_argument("task_id", help="父任务 ID")
    p_sub_list.set_defaults(func=cmd_sub_list)

    # sub show
    p_sub_show = sub_sub.add_parser("show", help="查看子任务详情")
    p_sub_show.add_argument("task_id", help="父任务 ID")
    p_sub_show.add_argument("sub_id", help="子任务 ID")
    p_sub_show.add_argument("--history", type=int, default=5, choices=range(1, 51),
                            metavar="N", help="历史记录条数 (1-50，默认 5)")
    p_sub_show.set_defaults(func=cmd_sub_show)

    # sub edit
    p_sub_edit = sub_sub.add_parser("edit", help="编辑子任务")
    p_sub_edit.add_argument("task_id", help="父任务 ID")
    p_sub_edit.add_argument("sub_id", help="子任务 ID")
    p_sub_edit.add_argument("-t", "--title", help="新标题")
    p_sub_edit.add_argument("-s", "--start", help="新开始日期")
    p_sub_edit.add_argument("-e", "--end", help="新截止日期")
    p_sub_edit.add_argument("--status", help="新状态")
    p_sub_edit.add_argument("-b", "--background", help="新背景描述")
    p_sub_edit.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_sub_edit.set_defaults(func=cmd_sub_edit)

    # sub delete
    p_sub_del = sub_sub.add_parser("delete", help="删除子任务")
    p_sub_del.add_argument("task_id", help="父任务 ID")
    p_sub_del.add_argument("sub_id", help="子任务 ID")
    p_sub_del.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_sub_del.set_defaults(func=cmd_sub_delete)

    # sub undo
    p_sub_undo = sub_sub.add_parser("undo", help="撤销删除子任务")
    p_sub_undo.add_argument("task_id", help="父任务 ID")
    p_sub_undo.add_argument("sub_id", help="子任务 ID")
    p_sub_undo.add_argument("-f", "--force", action="store_true", help="跳过确认")
    p_sub_undo.set_defaults(func=cmd_sub_undo)

    # ── todo cal ────────────────────────────────────────
    p_cal = sub.add_parser("cal", help="查看日历")
    p_cal.add_argument("month", nargs="?", default=None, help="YYYY-MM，默认当月")
    p_cal.set_defaults(func=cmd_cal)

    # ── todo search ─────────────────────────────────────
    p_search = sub.add_parser("search", help="搜索任务")
    p_search.add_argument("keyword", help="搜索关键字")
    p_search.set_defaults(func=cmd_search)

    # ── todo stats ──────────────────────────────────────
    p_stats = sub.add_parser("stats", help="统计概览")
    p_stats.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    original_argv = list(sys.argv[1:] if argv is None else argv)
    json_seen = "--json" in original_argv
    set_json_mode(json_seen)
    try:
        normalized_argv, data_dir, json_mode = _extract_global_options(original_argv)
    except _GlobalOptionError as exc:
        if json_seen:
            emit_error("usage_error", str(exc))
        else:
            print(f"todo: error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    set_json_mode(json_mode)
    parser = _build_parser()
    args = parser.parse_args(normalized_argv)
    args.data_dir = data_dir
    args.json = json_mode

    if not hasattr(args, "func"):
        if args.json:
            emit_error("usage_error", "missing command")
            return EXIT_USAGE
        parser.print_help()
        return EXIT_SUCCESS

    # 初始化数据目录
    if args.data_dir:
        set_data_dir(args.data_dir)
    else:
        clear_data_dir()

    # 分发执行
    try:
        args.func(args)
    except CliExit as exc:
        return exc.exit_code
    except StorageError as exc:
        if args.json:
            emit_error("data_file_error", str(exc))
        else:
            print(f"错误: {exc}", file=sys.stderr)
        return EXIT_DATA_FILE
    except KeyboardInterrupt:
        if args.json:
            emit_error("internal_error", "操作被中断", details={"signal": "KeyboardInterrupt"})
        else:
            print("", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception as exc:
        if args.json:
            emit_error(
                "internal_error",
                "命令执行失败",
                details={"type": type(exc).__name__},
            )
        else:
            print(f"错误: 命令执行失败: {exc}", file=sys.stderr)
        return EXIT_INTERNAL
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
