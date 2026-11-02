---
phase: 10
slug: compact-popup
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-02
---

# Phase 10 — Validation Strategy

Validation contract for `10-01-PLAN.md`. New cases were exercised: independent font-registered focused run 88 tests, OK, zero skips, 4.529 s; executor final full run 834 tests, OK, 11 platform skips, 42.323 s. Real KDE acceptance remains unperformed; see `10-VERIFICATION.md` for its explicit nonblocking Phase 10 boundary and Phase 11 research gate.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | Python stdlib unittest with PyQt6.QtTest |
| Config | Existing tests set QT_QPA_PLATFORM=offscreen |
| Quick command | `python -m unittest tests.test_config tests.test_settings_gui tests.test_app_gui` |
| Full command | `python -m unittest discover -s tests` |
| Availability | Host Python 3.14.3, PyQt6/Qt 6.11.0 imports verified during research |
| Estimated runtime | Full suite previously about 47 seconds; fresh phase runtime must be recorded |

## Sampling Rate

- Task 1: run config/settings tests after changes.
- Task 2: run app GUI/settings tests after changes.
- Task 3 and phase gate: run focused suite and full discovery; record actual counts, skips and failures.
- After any corrective change: repeat the affected verification before claiming it passes.
- Maximum planned feedback latency: 60 seconds; measure actual runtime, and report any overrun.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---|---|---|---|---|---|---|---|---|---|
| 10-01-01 | 01 | 1 | SET-02 | T-10-01 | Strict booleans; invalid edits preserve bytes; atomic merge and acknowledged rollback preserve prior values | Unit/native offscreen | `python -m unittest tests.test_config tests.test_settings_gui` | Yes; exercised | Passed in independent focused 88-test run |
| 10-01-02 | 01 | 1 | POP-06, SET-02 | T-10-02, T-10-03, T-10-04 | Bounded plain text; all useful senses precede details; late callbacks respect hidden context; cards retain original pair | Native offscreen integration | `python -m unittest tests.test_app_gui tests.test_settings_gui` | Yes; exercised | Passed in independent focused 88-test run |
| 10-01-03 | 01 | 1 | POP-06, SET-02 | T-10-01 through T-10-04 | Preserve history/cards/settings and report actual evidence limits | Regression suite | `python -m unittest discover -s tests` | Yes | Executor final full run 834 OK, 11 platform skips |

## Wave 0 Requirements

- [x] Extend `tests/test_config.py`: missing/invalid/default values, round-trip, unknown-key merge and invalid-write byte preservation for all three preferences.
- [x] Extend `tests/test_settings_gui.py`: accessible checkbox controls, snapshot/save/reopen, acknowledged apply and rollback, older snapshot compatibility.
- [x] Extend `tests/test_app_gui.py`: compact offline structured/unstructured articles, summary ordering across dictionaries, disclosure and bounds, hidden context on late events, independent meaning visibility, next request/reinitialized owner and unchanged cards/timer.

Existing test files, Qt fixture infrastructure and unittest are present; no framework installation or new test scaffolding is required. `wave_0_complete` becomes true only after the new behavior tests exist and are exercised. Red tests before implementation are valid TDD evidence; they are not acceptance passes.

## Native KDE and Reproduction Verifications

| Behavior | Requirement | Why separate | Instructions / current limit |
|---|---|---|---|
| Real KDE popup expansion, focus, placement and settings restart | POP-06, SET-02 | Offscreen Qt does not establish compositor behavior | Reuse owned-clone identity/network checks and native fixture workflow; verify compact offline result, expand/collapse, apply/reopen/restart and cards. Record agent acceptance separately from human feedback. |
| Owned-clone target preflight | Native acceptance | Protect original VM | Current preflight reports `Original VM must remain powered off` because original `arch-kde` is running. Do not control original VM or bypass guard. Native KDE acceptance stays pending; continue host verification. |
| Original Danila screenshot/article | POP-06 reproduction limit | Source input absent | Use explicit synthetic long-article fixtures. Do not claim original defect cause or photo reproduction established. |

These are KNOWN LIMITS, not unresolved design questions. A passing host suite does not close native KDE or missing-input evidence gaps.

## Validation Sign-Off

- [x] Every plan task has an automated verification command.
- [x] Sampling continuity: no task lacks an automated check.
- [x] Wave 0 maps required new cases into existing test files.
- [x] No watch-mode flags.
- [x] Planned feedback latency is at most 60 seconds, with fresh timing required.
- [x] `nyquist_compliant: true` records plan coverage, not test execution.
- [x] New tests exercised and execution counts recorded.
- [x] Native KDE evidence recorded or limitation retained explicitly in verification.

**Approval:** Independent agent verification 2026-11-02; Phase 10 passed with explicit host/target boundaries. Human and live KDE acceptance not claimed.
