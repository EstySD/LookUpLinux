---
phase: 05
slug: app
status: verified
threats_open: 0
asvs_level: 1
block_on: high
created: 2026-10-26
---

# Phase 05 — Security

One focused ASVS L1 pass over the fourteen declared threats in 05-01/02/03-PLAN.
No concrete blocking implementation gap found. All dispositions are `mitigate`;
no risk was newly accepted. Verification concerns presence of controls in the
current working source, including review fixes, not final VM acceptance.

## Trust boundaries

- Primary selection and screenshot pixels enter the serial lookup worker.
- Worker snapshots cross queued Qt signals; identity checks protect history
  and presentation against superseded or dismissed requests.
- Network/dictionary/user strings reach explicitly plain Qt widgets.
- Fixed per-user D-Bus IPC accepts a bounded activation token.
- Test-only instrumentation and physical VM input use isolated data/config
  roots; owned desktop/display resources require rollback and comparison.

## Threat register

| Threat | Severity | Disposition | Evidence / control | Status |
|---|---|---|---|---|
| T-05-01 | high | mitigate | `lookup/app.py:Engine.begin/current/dismiss` use monotonic identities and the same Condition as `_process.ready` history commit; `history` marker commits once; replacement/dismiss/burst barriers in `tests/test_app.py:85`, `:107` | closed |
| T-05-02 | high | mitigate | `lookup/app.py:Engine` has one serial worker, one pending slot, worker-owned resources and BoundedSemaphore(1); `_resources` sets SQLite busy_timeout=50; `lookup/translate.py:_context_request` releases admission only in actual completion finally, not join timeout; finite joins and cache-error handling; `tests/test_app.py:128`, `:158`, `tests/test_translate_ready.py:51`, `:72`, `:80`, `:108` | closed |
| T-05-03 | high | mitigate | `lookup/app.py:Source.freeze` bounds primary, rejects invalid/control text and keeps only in-memory consumed identity; freeze/resolve are followed by current-id checks before lookup, and primary consumption/history commit is acceptance guarded; pixels dropped before GUI signal; fixed worker errors; no clipboard writes or print/log calls in app/gui; `tests/test_app.py:189`, `:205` | closed |
| T-05-04 | medium | mitigate | `lookup/app.py:_process.snapshot` and `lookup/translate.py:lookup` detach result/timings with dataclasses.replace; accepted saved/count tuple reused for final event; `tests/test_translate_ready.py:28`, `tests/test_app.py:72` | closed |
| T-05-05 | high | mitigate | `lookup/gui.py:PlainBlock` uses setPlainText and setAcceptRichText(False); `Popup.label` sets QLabel PlainText; no rich-resource loader; fields selectable; hostile file-URL markup remains literal in `tests/test_app_gui.py:61` | closed |
| T-05-06 | high | mitigate | `lookup/gui.py:run` atomically registers unique SERVICE, fixed object and Trigger slot; forwarding accepts positive integer PID only; token validation caps UTF-8 at4096 and rejects NUL; startup removes activation env before child spawn; no arbitrary command slot or token logs | closed |
| T-05-07 | high | mitigate | `lookup/gui.py:Owner.receive` rechecks identity at queued delivery; dismiss invalidates engine; hide_for_capture differs from user dismiss; focus completion checks identity/revision/visibility; late context updates only visible current card; `tests/test_app_gui.py:71`, `:98`, `:144` | closed |
| T-05-08 | medium | mitigate | `lookup/gui.py:Popup` owns inactivity timer and intentional interaction filter; context-only receive does not call present/reset/focus; Owner.quit stops engine and polls completion via QTimer; `tests/test_app_gui.py:79`, `:98`, `:154`, `:171` | closed |
| T-05-09 | high | mitigate | `lookup/gui.py:desktop_text` validates absolute paths and escapes Exec, unique production desktop/service; platform window_action validates owned PID/UUID and action; lookup app/gui/entry contain no tool/unlock imports; harness-only registration checks conflict/ownership before changes | closed |
| T-05-10 | high | mitigate | `tools/check_app.py:PUBLIC` and Probe.Status redact arbitrary keys and return schema observations/booleans rather than raw widget or primary text; controlled public fixture is used for images. Independent visual review completed; root deleted29 exact owned PNG paths, including failed runs, verified final image paths absent and no owned runtime profiles remaining | closed; operational cleanup verified2026-10-27 |
| T-05-11 | high | mitigate | `tools/check_app.py:profile/environment/target` validate32-hex run id, isolate DB/dicts/cache/KDE config, refuse preexisting owners/conflicts/unowned desktop and snapshot before mutation; finish checks run id, process UID/start/env ownership, restores desktop/display and compares original theme hash; host finally independently releases input/attempts finish; `tests/test_check_app.py:17`, `:34` | closed |
| T-05-12 | high | mitigate | Same-lock guarded history commit and detached early publication in app.py; deterministic stale/burst barriers and real SQLite writer contention tests `tests/test_app.py:85`, `:107`, `:128`; queued dismissal test `tests/test_app_gui.py:71`; native harness independently reads DB and current window state | closed |
| T-05-13 | medium | mitigate | `tools/check_app.py:host` uses physical VBox keys/mouse, actual production CLI/owner, fixture primary and real screenshot/OCR; Probe exposes controlled independent state and target SQL reads history; accepted requires all REQUIRED_GATES and five restoration flags. Online/fault paths are explicitly instrumented and cannot be claimed as live-provider evidence. WR-01 exact-word predicate tested in `tests/test_check_app.py:29` | closed at control level; live verdict separate |
| T-05-14 | high | mitigate | `lookup/gui.py:MAX_DISPLAY_CHARS/MAX_DISPLAY_BLOCKS`, Popup.add enforce32000-character/128-block budget with visible truncation; source/context sections capped8000 each; PlainBlock wraps anywhere and outer scroll exposes bounded content; `tests/test_app_gui.py:122`, `:163`, `:171` | closed |

## Review remediation

- **CR-01:** PlainBlock.setText now refits at current viewport width and calls
  updateGeometry. Native late-context regression verifies content/outer scroll
  growth while count, presentation count and inactivity deadline stay unchanged.
- **WR-01:** Controlled `word` is whitelisted; correct_repeat requires both
  mode=ocr and exact key=word. Regression rejects unknown or another known key.
- Related long-article layout invalidation and fractional compositor geometry
  fixes are present as described in 05-REVIEW-FIXES.md. They do not introduce
  a new command, markup or persistence trust boundary.

## Operational condition: screenshots

The harness retains controlled images under host temporary
`lookup-phase05-visual-<run_id>` for the planned batch visual review. Root must
review then delete these images, including any from failed runs, and record
that cleanup before phase acceptance. This auditor did not inspect/delete
host images or assert final screenshot absence while the VM gates were active.
This is outstanding execution evidence, not a newly discovered source defect.

## Fresh validation and scope

`python -m unittest tests.test_app tests.test_app_gui tests.test_check_app tests.test_translate_ready`
completed **28 tests, OK, zero skips, 0.991s** on the Windows host. This includes
actual offscreen Qt rendering and the requested failure/race regressions.

No VM action, source edit, result rewrite or commit performed. The current or
previous gate result was not used as final acceptance evidence. Actual KDE
focus, physical input, restored settings and final absence of retained images
remain subject to root's separate live run and cleanup. Same-user session bus
and developer-owned instrumentation use the existing local-user trust model.

## Accepted risks / unmapped flags

No accepted risks added. No concrete unmapped blocker found in this focused
declared-threat verification. ASVS L1 control presence is not an exhaustive
concurrency, compositor or malicious same-user isolation proof.

## Audit trail

| Date | Threats reviewed | Blocking implementation gaps | Auditor |
|---|---|---|---|
| 2026-10-26 | 14 | 0 | Codex security auditor |

**Approval:** implementation security controls verified at ASVS L1; final live
acceptance and planned visual-artifact cleanup are separate.

## Final operational closure —2026-10-27

The earlier screenshot-cleanup condition is fulfilled by privacy_cleanup in
05-GATE-RESULTS.json and exact-path deletion of29 owned files. Five restoration
flags are true for the final main run and supplemental runs; no runtime profile
remains. No arbitrary query/token text or transient native image is committed.

Post-audit work-area correction reads fixed `plasmashell` class metadata through
kdotool and KWin getWindowInfo only. It limits output/UUID count, call deadlines,
checks compositor class/type, validates finite rectangle numbers, and performs
no panel/window action. The serial worker passes only numeric work-area metadata
to Qt. This adds no command-capable IPC or user-setting mutation. New regressions
cover fractional docks, floating edge gaps, other outputs and negative origins.
Independent final verifier must include this delta; no remaining operational
condition is asserted closed solely from the original control-presence audit.
