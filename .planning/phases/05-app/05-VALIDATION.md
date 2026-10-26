---
phase: 5
slug: app
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-26
---
# Phase5 — Validation Strategy
Planned checks,not passing evidence. Existing stdlib unittest; proposed quick
python -m unittest tests.test_app tests.test_app_gui tests.test_translate.
Full:python -m unittest;py -3.12 -m unittest;target python3 -m unittest.

| Requirement | Deterministic/local proof | Actual production VM proof |
|---|---|---|
| TRIG-02 | Events delay A;start B or dismiss;release A;no stale UI/history;burst queue latest;bounded context worker count | Repeated hotkeys and close during pending request |
| TRIG-03 | Atomic owner race,warm client,no duplicate worker,quit closes worker DB/dicts | Physical hotkey warm/cold same owner,tray menu/quit |
| CAPT-02 | New selection once,unchanged→OCR,absent/invalid resets,1000char bounds;no writes to clipboard | Known public actual primary/new/repeat/empty selection |
| POP-01 | Ordered Article fields,no invented metadata,source+translation,count only after commit;word/phrase once,sentence never | Public OCR/selection→useful card+SQLite context/count |
| POP-02 | Generation invalidation on all dismissal paths;programmatic hide distinguished | Escape,outside/focus loss,inactivity;no late reopen |
| POP-03 | Fixed missing-tool/platform/network/blocked/timeout states;context/save failure preserve article | Controlled failures and actual readable Russian state |
| POP-05 | Plain selectable text,scroll bound,accessible names,palette events | Real Breeze light/dark,four scales,monitor edges |

Additional proofs:translate on_ready snapshot independent from later mutation;
save=False caches/meta allowed but no history;ready/final exactly one commit;
competing SQLite writer bounds guard wait and reports save_error;all connection
and DictSet access occurs in worker thread. Core -S imports and CLI unchanged.
Capture frozen before loading;mock order plus actual public scene proves no
self-capture. Token/log/artifact privacy;no retained screenshot or clipboard copy.

Measure first useful card separately from loading/final context. Existing finite
context join means queued latest may wait;record real latency,do not claim1.5s
from Phase4's capture/OCR benchmark. UI-SPEC dimensions/timeout are acceptance
inputs before plans. Screenshots for UI inspection only controlled fixtures;
remove after bounded review. No human-testing claim under agent --auto acceptance.

Gate:all requirement checks,full regressions,actual production VM route,security
and UI evidence. No skipped integration test substitutes for observed behavior.
