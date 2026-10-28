---
phase: 07
slug: settings-package
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-28
---

# Phase 7 — Validation Strategy

## Test Infrastructure

Existing Python stdlib unittest suite; native PyQt6/KDE checks run in an owned full VM clone. No framework installation required. Quick checks run focused modules named by each plan; full command: python -m unittest discover -s tests. Target full suite enables LOOKUP_TEST_OCR=1 and LOOKUP_TEST_DICTS for the real Mueller installation. Expected full run under 90 seconds; long native/package/login checks report progress separately.

## Sampling Rate

- Each implementation task runs its focused regression tests before commit.
- Each integration wave runs the full suite; final acceptance requires fresh host and target results.
- No three consecutive tasks without automated feedback; no watch mode.

## Per-Task Verification Map

Every implementation task creates behavioral tests beside its contract; existing unittest/Qt infrastructure requires no separate scaffold wave. Exact task mapping follows. Structural Nyquist compliance is established here; actual verification/sign-off remains pending execution.

| Task | Requirements | Automated checks | Native acceptance |
|---|---|---|---|
| 01-1 | SET-01, TRIG-04 | python -m unittest tests.test_config tests.test_paths tests.test_core_imports | Atomic save/field preservation |
| 01-2 | SET-01 | python -m unittest tests.test_app tests.test_translate_ready tests.test_learning tests.test_config | Monotonic reload, owning thread, stale reply refusal |
| 02-1 | SET-01, INST-01 | python -m unittest tests.test_lifecycle tests.test_app_gui tests.test_cli | Actual physical old/new keys in 05 |
| 02-2 | TRIG-04, INST-01 | python -m unittest tests.test_lifecycle tests.test_platform tests.test_cli tests.test_core_imports | Actual login/private helper in 05 |
| 03-1 | SET-01 | python -m unittest tests.test_settings_gui tests.test_config tests.test_core_imports | Approved native controls/themes/keyboard |
| 03-2 | SET-01, TRIG-04 | python -m unittest tests.test_settings_gui tests.test_app_gui tests.test_app tests.test_learning_gui | Applied ack, timeout/order/online oracle in 05 |
| 04-1 | INST-01, TRIG-04 | python -m unittest tests.test_package tests.test_lifecycle tests.test_platform | Actual staging/makepkg/helper/Mueller/capture/remove |
| 04-2 | INST-02 | python -m unittest tests.test_doctor tests.test_cli tests.test_core_imports tests.test_privacy | Actual healthy/missing/damaged/offline doctor |
| 04-3 | INST-02 | python -m unittest tests.test_package tests.test_doctor tests.test_cli | README followed on clone |
| 05-1 | SET-01 | python -m unittest tests.test_check_settings_app tests.test_settings_gui tests.test_app tests.test_lifecycle | Real owned clone/native settings gates |
| 05-2 | SET-01, TRIG-04, INST-01, INST-02 | python -m unittest discover -s tests | Actual install/login enabled+disabled/physical keys/capture/removal/data retention |

Wave ownership: 01 config/app; 02 lifecycle/platform/CLI/desktop compatibility; wave3 03 settings/gui and 04 package/doctor/CLI/docs have no shared modified files; 05 owns acceptance harnesses. Plan03 and plan04 both depend on plan02, so earlier CLI/gui edits are complete before their consumers.

## Source Coverage Audit

| Source | Item | Plans | Status |
|---|---|---|---|
| GOAL/REQ | SET-01 effective native settings | 01,02,03,05 | COVERED |
| REQ | TRIG-04 real configurable login | 01,02,04,05 | COVERED |
| REQ | INST-01 install/helper/Mueller/key/remove | 02,04,05 | COVERED |
| REQ | INST-02 doctor/Russian README | 04,05 | COVERED |
| CONTEXT | D-01 native settings | 03,05 | COVERED |
| CONTEXT | D-02 compatible atomic config | 01,03 | COVERED |
| CONTEXT | D-03 worker reload/monotonic stale protection | 01,03,05 | COVERED |
| CONTEXT | D-04 actual key/conflict/override/rollback | 02,03,05 | COVERED |
| CONTEXT | D-05 source/installed config-gated autostart | 01,02,04,05 | COVERED |
| CONTEXT | D-06 reproducible private helper/Mueller/licenses | 02,04,05 | COVERED |
| CONTEXT | D-07 safe package removal/data retention | 02,04,05 | COVERED |
| CONTEXT | D-08 private read-only doctor | 04,05 | COVERED |
| CONTEXT | D-09 fresh-reader Russian guide | 04,05 | COVERED |
| CONTEXT | D-10 isolated clone/native/login/package agent evidence | 05 | COVERED |
| RESEARCH | Fixed KDE action, single-chord readback, inherited override | 02,03,05 | COVERED |
| RESEARCH | Pinned third-party hashes, attribution uncertainty, installed capture identity | 04,05 | COVERED |
| RESEARCH | Full clone/no snapshots, unique MAC/SSH forwarding, real graphical session | 05 | COVERED |

Deferred real games, sustained performance and clean-snapshot reliability acceptance remain Phase8; no v2 feature is planned.

## Wave 0 Requirements

Implementation plans add focused unittest coverage alongside each observable contract. Existing test infrastructure and VM tools suffice. Native scripts must isolate XDG directories before Qt creation and report every required gate and cleanup outcome.

## Environment Verification

Use an owned full clone of powered-off arch-kde, with unique MAC and forwarding port. Preserve the original VM, unrelated shortcuts and user data. Record clone name, package versions, actual login evidence, owned service identities and baseline. Package removal preserves seeded history/cards/config and unrelated entries. Cached inert shortcut preferences must be distinguished from active registration. Report agent acceptance, never human testing. Mueller license-version uncertainty remains explicit until primary evidence resolves it.

## Validation Sign-Off

- [ ] All plan tasks map to automated checks or bounded native gates.
- [ ] Focused regression and fresh full host/target suite evidence saved.
- [ ] Physical key, real login and actual package install/remove evidence saved.
- [ ] Cleanup and preservation assertions pass; unresolved limits recorded honestly.
- [ ] nyquist_compliant updated from actual task mapping/evidence.

Approval: pending agent verification under --auto.
