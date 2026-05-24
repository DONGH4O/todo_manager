## Summary

- 

## Validation

- [ ] Python compileall: `python -m compileall engine cli gui scripts`
- [ ] Python tests: `python -m pytest -q`
- [ ] CLI smoke: `todo --help` / `python scripts/ci_cli_smoke.py`
- [ ] React checks: `npm run lint` / `npm run typecheck` / `npm run build`
- [ ] Release dry-run, if touched: `python scripts/build.py react` / `python scripts/smoke_release.py --react-only`

## Release Impact

- [ ] README/docs updated when commands, release behavior, or milestone state changed.
- [ ] No `.venv`, `dist`, caches, local data, screenshots, or temporary files are included.
- [ ] Windows/macOS manual follow-up is recorded when a real desktop window or platform package cannot be validated in CI.
