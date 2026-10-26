---
phase: 04
slug: vm
status: verified
threats_open: 0
threats_total: 14
threats_closed: 14
asvs_level: 1
block_on: high
created: 2026-10-26
---

# Phase 04 — Security

ASVS L1 verification of T-04-01 through T-04-14 from the three phase plans.
All dispositions are `mitigate`; no new risk acceptance was made. Checked
actual implementation after the CR-01/02/03 fixes. This report verifies
security controls, not completion of the separately running VM experiment.

## Trust boundaries

- KDE command output and screenshot metadata/pixels enter bounded parsers.
- Subprocesses and screenshot FDs require finite waits and owned cleanup.
- Per-user session D-Bus carries fixed methods and a bounded activation token.
- Host automation modifies one VM's owned shortcut/desktop resources and
  display scale, then compares restoration against its recorded snapshot.
- Evidence contains public fixture recognition, geometry and event state;
  screenshots, arbitrary OCR text and primary-selection content are excluded.

## Threat verification

| Threat | Severity | Disposition | Verified control and evidence | Status |
|---|---|---|---|---|
| T-04-01 | high | mitigate | `lookup/platform.py:_numbers`, `Monitor.__post_init__`, `parse_monitors`, `image_point` validate finite geometry and map using actual image dimensions; negative-origin/scale tests in `tests/test_platform.py:15` | closed |
| T-04-02 | high | mitigate | `lookup/platform.py:run` uses argv with `shell=False`; `owned_window` validates PID/UUID and `window_action` checks membership/action/coordinate arguments before executing; ownership rejection test at `tests/test_platform.py:67` | closed |
| T-04-03 | high | mitigate | `lookup/platform.py:run` applies deadline, byte cap, process-group/tree termination and unbuffered stdout cleanup; `read_primary` uses .5s and 64 KiB; deadline and descendant regressions at `tests/test_platform.py:45`, `:55` | closed |
| T-04-04 | high | mitigate | `lookup/capture.py:raw_layout` validates raw format, strict dimensions/stride, finite scale and byte/pixel limits; `raw_image` requires exact length and detaches storage; `_screenshot2` concurrently drains a capped FD with select/deadline and finally closes FDs; metadata/lifetime tests at `tests/test_platform.py:90`, `:98` | closed |
| T-04-05 | high | mitigate | `lookup/capture.py:capture_monitor` keeps ScreenShot2 PNG in memory and scopes Spectacle output to TemporaryDirectory; `_prepare_image` retains a bounded QBuffer; `read_primary` only reads, and harness primary evidence records elapsed/offered rather than text; fixed library errors | closed |
| T-04-06 | high | mitigate | `tools/vm_spike.py:main` atomically registers fixed per-user service and object/interface, loser forwards trigger; Trigger accepts only bounded valid token, returns owner PID; setup refuses preexisting bus owners; fixed Qt slot signatures bound IPC shape | closed |
| T-04-07 | medium | mitigate | `tools/vm_spike.py:Owner.Trigger` sets worker before queued start and refuses overlap; capture runs in QThread while Status/Quit remain event-loop slots; worker resources retained until finished | closed |
| T-04-08 | high | mitigate | `tools/vm_spike.py:valid_token` caps UTF-8 at 4096 and rejects NUL; startup removes activation variables before spawning children; token is not included in status/evidence; pipeline exposes only the literal controlled word english or null; tests at `tests/test_vm_spike.py:12`, `:24` | closed |
| T-04-09 | high | mitigate | `tools/vm_spike.py:desktop_text` requires absolute non-control paths and Desktop Exec escaping; unique desktop/service constants; `tools/check_vm_spike.py:target` checks binding availability and refuses unowned desktop; restore checks ownership marker and compares bytes | closed |
| T-04-10 | medium | mitigate | `tools/vm_spike.py:position_popup` sends owned PID/UUID through validated `window_action`; no global focus-policy writes; owner retains tray/menu/popup/worker and delays Quit until worker completes | closed |
| T-04-11 | high | mitigate | Active implementation uses validated kdotool commands, not a KWin script or arbitrary script receiver. No fallback script is installed or loaded. The conditional fallback attack surface is absent; future fallback implementation requires its own ownership/receiver/unload checks | closed — inactive fallback |
| T-04-12 | high | mitigate | `tools/check_vm_spike.py:setup_owned` snapshots before mutation and rolls back setup failures; per-run UUID ties restore to its own snapshot; child PID/start-time/UID/cmdline checks precede termination; restore compares display fields, desktop bytes, stopped processes and shortcut availability; failed restoration retains snapshot | closed |
| T-04-13 | high | mitigate | `tools/vm_spike.py:pipeline` returns english only on controlled fixture match, never arbitrary recognized word; no retained frames; `target('primary')` records only presence/timing; `Status` contains fixed state/results and bounded event slice, not tokens/selection text; privacy regression at `tests/test_vm_spike.py:24` | closed |
| T-04-14 | high | mitigate | `tools/check_vm_spike.py:wait_for` bounds polling; host marks setup attempted before request, independently guards final key release, then attempts owned restore and writes evidence; `accepted` rejects error/restoration_error/key_release_error and requires all four restoration flags; failure regressions at `tests/test_vm_spike.py:57`, `:73`, `:90` | closed |

## Review remediation

- **CR-01:** buffered read replaced by `os.read` over unbuffered FileIO;
  POSIX child uses a new session and finally kills its process group, Windows
  attempts taskkill /T; bounded-reader descendant regression now passes.
- **CR-02:** setup persists ownership before mutation and after child launch,
  restores on exceptions, and host attempts finish even when setup response
  fails. Final key release has its own exception guard, so it cannot suppress
  restore/evidence writing. Both required mocked failure regressions pass.
- **CR-03:** shared `accepted` predicate requires display_restored,
  desktop_restored, processes_stopped and shortcut_restored to be exactly true,
  with no restoration/key-release error. Regression rejects each false flag.

## Verification and limits

Fresh command: `python -m unittest tests.test_platform tests.test_vm_spike`.
Result: **17 tests, OK, 0 skips, 0.994s** on the Windows host.

No VM interaction, source modification, user-file access or live-result
rewrite was performed by this audit. No live capture/desktop restoration
outcome is asserted here. POSIX cleanup and actual compositor/session behavior
remain the responsibility of the separate live gate run. ASVS L1 verifies
presence of declared controls; it is not an exhaustive race/availability proof.
The D-Bus boundary assumes the existing same-user session trust model.

## Accepted risks and unmapped flags

No accepted risks added. No concrete unmapped blocking threat identified in
the requested implementation/remediation scope.

## Audit trail

| Date | Total | Closed | Open blocking | Auditor |
|---|---|---|---|---|
| 2026-10-26 | 14 | 14 | 0 | Codex security auditor |

**Approval:** security controls verified at ASVS L1; live acceptance is separate.
