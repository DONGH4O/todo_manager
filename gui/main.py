"""D3 GUI 入口 — python -m todo_manager.gui"""

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo-gui",
        description="Todo Manager 图形界面",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="指定数据目录（默认开发态为项目 data，打包后为系统应用数据目录）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    from todo_manager.gui.app import run_app

    run_app(data_dir=args.data_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
