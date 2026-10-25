# Phase 3 — Existing Patterns

Source inspection: 2026-10-25. No implementation edits.

| New responsibility | Closest existing analog | Apply |
|---|---|---|
| OCR records and quiet typed errors | lookup/dicts.py Article/SearchResult/DictError; lookup/online.py TranslateError | Immutable dataclasses; fixed reason codes, suppressed exception details |
| TSV parse and shape validation | lookup/online.py parse_google/parse_mymemory | Reject malformed structures; isolate transport from parsing |
| Word acceptance | lookup/normalize.py normalize | Reuse Latin/digit/punctuation rules; do not normalize displayed context |
| Candidate resolution | lookup/dicts.py DictSet.find and SearchResult.__bool__ | Offline phrase probes before one final query |
| Final lookup/context/save | lookup/translate.py lookup | Use existing keyword-only options and one final save/count |
| CLI errors/output/timing | lookup/__main__.py main/format_result | CLI owns print, fixed stderr warnings, exit 0/1/2, finally closes resources |
| Optional image dependency | Existing core import contract in tests/test_core_imports.py | Lazy PyQt6 import only in image adapter; extend python -S test |
| Isolated persistence tests | tests/_support.py make_tempdir | Point LOOKUP_* into throwaway root before resources open |
| Forbidden network assertions | tests/_support.py forbid_network | Shared mock covers urlopen and custom opener calls |
| Independent fixtures | tests/_stardict_writer.py, _dsl_writer.py, _mdx_writer.py | Add test-only TSV records and phrase dictionary independently of OCR implementation |

Recommended file scope: lookup/ocr.py for the pure core plus lazy image/process
adapter; lookup/__main__.py for CLI wiring; test_ocr.py, test_ocr_image.py,
test_ocr_cli.py for boundary-specific behavior; tools/ for fixture/calibration
generation. Keep geometry pure and do not add desktop capture in this phase.

Unresolved measurements: preprocessing parameters and selection thresholds.
No measured OCR accuracy is claimed by this pattern map.
