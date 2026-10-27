---
phase: 5
slug: app
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-26
---
# Phase5 — Validation Strategy
Executed checks are recorded in05-GATE-RESULTS.json,05-EXTRA-GATES.json and
05-VM-RESULTS.md. Existing stdlib unittest; quick
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
hold one context response beyond finite join, issue many later requests, require
one live context job and explicit busy context with bounded Quit. Exercise
cache/meta read/write failure with successful online/main/context results;
preserve content and fixed cache_error without retrying network or history.
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

## Executable Task / Multi-Source Coverage

| Task | Required coverage | Automated verification |
|---|---|---|
| 05-01/T1 | CAPT-02/POP-01/POP-03; D-01/D-02/D-04/D-08; detached early callback and source freeze | python -m unittest tests.test_translate tests.test_app tests.test_core_imports |
| 05-01/T2 | TRIG-02/POP-02/POP-01; D-03/D-04/D-07/D-08; linearized history, coalescing, ownership, busyDB | python -m unittest tests.test_app tests.test_translate tests.test_core_imports |
| 05-02/T1 | POP-01/02/03/05/TRIG-02; D-03/D-05/D-06/D-08; all approved UI-SPEC states/fields/timer/theme/plaintext rules | python -m unittest tests.test_app_gui tests.test_app |
| 05-02/T2 | TRIG-03/CAPT-02; D-01/D-07/D-09; atomic owner/warm QCore client/tray/lazy CLI/quit | python -m unittest tests.test_app_gui tests.test_cli tests.test_core_imports tests.test_app |
| 05-03/T1 | D-03/D-04/D-09/D-10; deterministic race/error/rollback completion and production harness | python -m unittest tests.test_app tests.test_app_gui tests.test_translate |
| 05-03/T2 | All seven requirements, all five roadmap criteria, D-01..D-10; actual production/primary/keys/theme/scales/errors/restoration | python3 tools/check_app.py --output /tmp/lookup-phase05-results (target with host input) |

GOAL/ROADMAP, REQ TRIG-02/TRIG-03/CAPT-02/POP-01/POP-02/POP-03/POP-05,
RESEARCH ownership/cache/finite-context/guard/source-order/privacy constraints,
CONTEXT D-01..D-10 and approved UI-SPEC/PRODUCT/DESIGN/Linux evidence contracts
are all covered by the map. Original Lookupper freshness/cancellation remain
unverified evidence Q04–Q06; these plans implement the accepted Linux contract,
not a fabricated original behavior. Phase6/7 surfaces, packaging and settings
remain excluded. No required source item is missing. Waves1/2/3 are sequential
because the UI consumes the engine and actual integration consumes both.
