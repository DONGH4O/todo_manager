"""D3 GUI 入口 — python -m todo_manager.gui"""

import argparse
import sys


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo-gui",
        description="Todo Manager React 桌面界面",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help="指定数据目录（默认开发态为项目 data，打包后为系统应用数据目录）",
    )
    parser.add_argument(
        "--react",
        action="store_true",
        help="兼容旧命令；React 桌面界面现在是默认 GUI",
    )
    parser.add_argument(
        "--react-root",
        default=None,
        help="指定 React 静态导出目录或 index.html，用于桌面 shell smoke",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    from todo_manager.gui.react_shell import run_react_app

    return run_react_app(data_dir=args.data_dir, react_root=args.react_root)


if __name__ == "__main__":
    sys.exit(main())
