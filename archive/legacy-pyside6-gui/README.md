# Legacy PySide6 Widget GUI Archive

This folder keeps the pre-cutover PySide6 widget GUI for historical reference only.

Current status:

- Active GUI: `gui/main.py` -> `gui/react_shell.py` -> React desktop renderer in `frontend/`.
- Legacy widget GUI source: `archive/legacy-pyside6-gui/gui/`.
- Legacy widget GUI pytest file: `archive/legacy-pyside6-gui/tests/legacy_gui_pytest.py`.
- The legacy tests are intentionally renamed so normal `pytest` runs do not collect them.

Do not add this archive back to future release, GitHub, npm, or milestone acceptance paths unless the project explicitly decides to restore the widget GUI.
