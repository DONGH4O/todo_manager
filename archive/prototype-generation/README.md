# Prototype Generation Archive

> Archived during M0 on 2026-05-19.

This folder preserves the previous prototype generation scripts without keeping
them on the active source path.

Archived files:

- `generate_prototype.py.broken`
- `_write_proto.py.broken`

Reason:

- `generate_prototype.py` fails to compile because of an unterminated
  triple-quoted string.
- `_write_proto.py` contains malformed string syntax and an absolute local
  output path.
- The generated artifact `prototype.html` still exists at the project root and
  remains the current static GUI prototype reference.

Decision:

- Do not repair this generator in M0.
- Rebuild or replace the prototype generation workflow during M4 GUI/UX
  redesign if a reproducible prototype is still needed.

M2 review:

- Rechecked on 2026-05-19 during source reliability audit.
- The broken scripts remain outside the active source path, so
  `python -m compileall engine cli gui scripts` does not include them.
- No additional repair is needed before M4 because `prototype.html` remains
  the active static prototype reference.
