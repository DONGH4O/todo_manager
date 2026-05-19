"""入口：python -m todo_manager.cli"""
import sys

from todo_manager.cli.main import main


if __name__ == "__main__":
    sys.exit(main())
