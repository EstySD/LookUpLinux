# Contributing

English and Russian bug reports, documentation fixes and focused pull requests
are welcome. Check existing issues first; discuss large changes before implementation.

## Development

Use Python 3.12 or newer. Core modules use the standard library. GUI work needs
PyQt6; OCR integration needs Tesseract and English language data. The full app
also needs the Arch/KDE Wayland dependencies in the public package recipe.
Windows core tests do not imply a Windows application port.

```bash
python -m pip install PyQt6
python -m unittest discover -s tests -v
python -m lookup --help
```

For headless GUI tests set `QT_QPA_PLATFORM=offscreen` before running tests:
`export QT_QPA_PLATFORM=offscreen` on Linux or
`$env:QT_QPA_PLATFORM='offscreen'` in PowerShell.
Record skipped external-dictionary or real-desktop checks. Unit tests do not
include historical VM/probe checks when the public source archive lacks their
private planning artifacts; these checks are explicitly skipped. Tests do not
verify global shortcuts, screen capture or fullscreen games; check those in a
KDE Wayland session when changing their behavior.

## Pull requests

- Keep changes focused and follow surrounding Python style.
- Add regression tests for behavior changes and run relevant tests after edits.
- Explain the user-visible result and give verification commands and results.
- Exclude private dictionaries, personal screenshots, databases, credentials and agent state.
- Preserve upstream notices. Original-code contributions use GPL-3.0-or-later.

Use synthetic fixtures or data you may redistribute. Do not attach commercial
dictionaries to reproduce parser bugs. See [Releasing](docs/RELEASING.md) for
release steps and [Security](SECURITY.md) for vulnerability reports.
