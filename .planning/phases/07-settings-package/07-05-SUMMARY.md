---
phase: 07-settings-package
plan: 05
subsystem: native-package-acceptance
tags:
  - kde-wayland
  - virtualbox
  - settings
  - package
  - login
requires:
  - phase: 07-03
    provides: Native acknowledged Settings and dictionary-folder rescan
  - phase: 07-04
    provides: Deterministic package staging and read-only doctor
provides:
  - Actual installed native settings, graphical login and removal evidence
  - Strict report with fourteen product gates and an explicit original-disk preservation limit
  - Owned-clone input and installed-native observation harnesses
affects:
  - phase-verification
  - 08-vm
tech-stack:
  added: []
  patterns:
    - Actual separate SDDM account with isolated XDG before Qt
    - Physical input separated from explicit controlled failure and network oracles
    - Missing or false gates and cleanup cannot become accepted success
key-files:
  created:
    - tools/check_settings_app.py
    - tools/check_package_vm.ps1
    - tests/test_check_settings_app.py
    - .planning/phases/07-settings-package/07-native-report.json
  modified: []
key-decisions:
  - Preserve strict accepted=false when original byte preservation cannot be demonstrated.
  - Distinguish actual package removal of files and keys from termination of an already loaded daemon.
  - Strip cross-user SUDO ownership variables only in the controlled verification environment.
  - Keep the powered-off owned clone and synthetic retained data for independent review.
requirements-completed: []
duration: not-recorded
completed: 2026-10-29
status: executed-with-verification-limit
---

# Phase 7 Plan 05: Installed Native and Login Acceptance Summary

**The installed package passed fourteen native/product gates, including physical shortcut capture, effective Settings, real graphical logins and package removal; the strict report remains false because a separate original-VM GUI run changed its baseline disk.**

Implementation: `tools/check_settings_app.py` and `tools/check_package_vm.ps1`.

Authoritative bounded result: `.planning/phases/07-settings-package/07-native-report.json`.

## Task Commits

1. Task 1 RED acceptance guards: `113efe6`.
2. Task 1 GREEN native harness and guards: `1f6b029`.
3. Task 2 actual package/login/removal evidence: `2560af8`.

## Accomplishments

- Reused the independent full clone `lookup-gsd-07`, UUID `cf207909-94b5-4b49-8bd8-ccff973c1dc8`, disk UUID `2712d710-daaa-449c-843d-d570091127bc`, MAC `080027A05376`, SSH NAT port 2227. Every acceptance VBox control targeted this clone. Input helper checks exact clone identity/network and requires the original powered off; it never boots, reverts or deletes the original.
- Created the controlled `lookup07` UID1001 account and genuine SDDM Wayland sessions. XDG config/cache/data live under its owned home before Qt imports; actual runtime socket/bus remain those of its graphical session. No personal arch profile, clipboard contents or dictionary collection was read for acceptance.
- Actual `makepkg -si --noconfirm` installed the final production revision `a48fce1`. Source archive SHA256 `4c1eb43ff29de4c14e0fcbb8cf92e99119737d99193506ec8acdbc6ea0adb380`; package SHA256 `62d575bb455ad72624019d1d8f0a9e0939353bc6e889015d071df4202f6fb116`. Installed Settings SHA256 `0c1b472f9b9d321cb064e03cda8d63f5cb88939e7a4a047f651f77a52086e103`. Desktop validation passed; private helper ldd had no missing library; system Mueller worked without checkout cwd/PYTHONPATH.
- Plain installed daemon and physical VBox shortcut over the public river fixture produced actual authorized ScreenShot2/Tesseract OCR, a useful Mueller article, and `bank` count1 with `They waited by the bank of the river.` No capture authorization bypass was used. This initial physical proof used `17b3b22`; final `a48fce1` changes the empty-root Settings branch, leaving the capture/OCR/lifecycle path unchanged. Final installed native Settings, doctor, login and removal evidence uses `a48fce1`.
- Settings changed the actual key from D to E: physical old D left presentations at2, physical new E advanced to4. Native Up-button reordering returned SECOND/FIRST articles; disabling first returned SECOND alone. Actual folder activation opened Dolphin at the displayed destination (`isUrlOpen` true), copied complete StarDict fixtures in subfolders, and unchanged-field Apply acknowledged rescan in the same Engine before its next lookup.
- Controlled provider oracle proved no new calls after switching online off (1 to1). Actual 2-second popup timeout measured 2.073 seconds. Apply invalidated a held old lookup; its stale ready result never appeared. Controlled save/resource/rollback injections rendered `save_failed`, `runtime_failed`, `rollback_config`, `rollback_shortcut`; actual occupied Meta+L produced `shortcut_conflict`. Actual E was repaired afterward. Missing dictionary, keyboard Space/Return Apply, native light/dark and 450x420 at DPR1.5 were inspected.
- Genuine enabled login: session48, SDDM Wayland, singleton PID2418, `/usr/bin/python /usr/bin/lookup --autostart`, observed for13.791 seconds. Before login the controlled harness quit and owner=false was verified. Disabled login: false saved through physical native Settings, actual tray Exit, owner=false before restarting SDDM; new session22 stayed ownerless for12.143 seconds. No observer invoked the product during either interval.
- Actual `pacman -R` ran with daemon2418 still loaded. Automatic registry refresh removed the owned action/key before any manual refresh. Physical E produced no popup or DB mutation; unrelated physical U updated its synthetic marker. Package/helper/Mueller/autostart files disappeared. Config, SQLite history/cards and unrelated desktop hashes remained identical. A subsequent supported `kbuildsycoca6` refresh exited0 and retained absent keys. Actual tray Exit then stopped the surviving daemon; removal itself is not claimed to terminate loaded code.
- Actual installed doctor healthy/offline cases exited0 and missing-tool/damaged-dictionary cases exited1. All four isolated inventories remained unchanged and temporary profiles were removed. The owned clone was gracefully powered off and preserved with synthetic retained data for review.

Task execution and recording are finished. Global requirement/state acceptance is left to the parent orchestrator; this summary does not override the failed preservation predicate.

## Validation Results

- Fresh final focused command `python -m unittest tests.test_check_settings_app tests.test_settings_gui tests.test_app tests.test_lifecycle`: **51 tests OK, 1.537s**. Invalid reports, extra false gates, missing/false/skipped gates, wrong mode and failed cleanup are rejected.
- Host full discovery: **701 tests OK, 8 skips, 30.036s, Python exit0**, `07-final-host-tests.txt`. Skips are the four POSIX process checks, two real-Mueller checks and two actual OCR/opt-in checks.
- Target full discovery: **701 tests OK, zero skips, 36.974s, Python exit0**, `07-final-target-tests.txt`, with `LOOKUP_TEST_OCR=1` and `LOOKUP_TEST_DICTS=/usr/share/lookup/dicts/mueller7`. Existing deliberately negative multiprocessing deadline coverage may print SemLock startup FileNotFoundError teardown noise; positive concurrent writers passed. Raw log retained.
- Final report: **14/14 product gates true, 5/6 cleanup predicates true, strict accepted=false**. The failed cleanup predicate is `original_preserved`; the validator was not weakened. Both VMs were observed powered off at the end, and no owned harness/daemon process remained.
- Visual artifacts: `07-native-first.png`, `07-autostart-disabled-save.png`, `07-settings-light.png`, `07-settings-dark.png`, `07-settings-scaled-dark.png`, `07-settings-rollback-key.png` and `07-after-removal-key.png`. Native structured details are in `07-native-suite-state.json`, `07-native-extra-cases.json`, `07-native-scaled.json`, the two login reports and `07-doctor-cases.json`.
- Source/provider network success is not substituted for an offline policy check. Failure injection is explicitly identified; physical capture/key, actual logins and actual package removal use real installed paths. This is agent acceptance evidence, not human or Phase8 game/performance acceptance.

## Deviations from Plan

### Auto-fixed verification issues

1. **[Rule 1 - Harness bug] Normal native edit signals.** Initial takeItem/addItem reordered the view without making Apply eligible; the unchanged worker result was rejected. Replaced it with actual native Up-button clicks. An initially invalid injected provider error reason was corrected to `no_network` before accepted policy evidence.
2. **[Rule 1 - Harness bug] Fresh command and retry handling.** Cleared only owned stale command/state files before new instrumented owners, handled unchanged Apply, removed duplicate missing identities on repeat checks, and made keyboard Apply change a value. Rejected development runs were not counted as accepted native gates.
3. **[Rule 3 - Environment] Cross-user sudo cache ownership.** `kbuildsycoca6` returned255 because inherited `SUDO_UID=1000` made UID1001 attempt to chown its cache to arch. [Official KDE kservice source](https://github.com/KDE/kservice/blob/v6.31.0/src/sycoca/kbuildsycoca.cpp#L387) explains that behavior. Stripping SUDO ownership variables in the owned verification environment restored actual refresh exit0. No production workaround or personal config change was made.
4. **[Rule 3 - Observer] Post-removal imports.** The first post-removal observer could not import the inaccessible arch checkout. Replaced it with read-only system QtDBus registry observation before explicit refresh; no failed observer result was promoted.
5. **[Verification tolerance] VM scheduling.** An initial tight timeout assertion was rejected during development. The bounded allowance is1.5..4 seconds for nominal2; the final observed hide was2.073 seconds. The product timer callback was never replaced.

### Original disk preservation limit

Preparation recorded the original powered off and its VDI SHA256 unchanged at `9f2b4a34fe8ae0f73db8df281f9414a68c9e9483e3d981b7a288f53c5b18fd1c` (9848390144 bytes). Final independent root hash is `fd3c5382d73a5ebdf849c5abe2e974c227398b1389b5738d5729714aa9c401b1` (9958490624 bytes). Its final byte identity therefore **does not pass**.

Read-only original logs show a separate `VirtualBoxVM.exe` GUI run, PID6048, opened2026-10-28T15:55:44.421707200Z and shut down about16:11:09Z; original VDI lastwrite is16:11:07Z. The actor is not established. Independent base disks remained attached only to their respective VMs; acceptance controls used the clone UUID and headless workflow. No source restoration, reversion, deletion or compensating original write was attempted. Earlier automatic removal of13 transient original GuestProperties during preparation is separately recorded in `07-clone-preparation.json`; it does not explain away the later disk change.

This is an explicit non-product verification limit for parent review under --auto, not a passing original-preservation claim. Both VMs end powered off. No human acceptance is asserted.

## Known Limits and Retention

- The original disk predicate keeps strict acceptance false. No source/data restoration was authorized or performed.
- Own project licensing remains undeclared, and Mueller's upstream GPL notice lacks an exact version; package notices retain the uncertainty. No redistribution clearance is claimed.
- Only the owned clone/account/synthetic retained data remain for review. Runtime fixture processes and all held input were stopped/released; doctor temporary profiles were removed. Original/personal profiles were not cleaned.
- No OCR algorithm change occurred in this unit, so the prior144-image matrix was not repeated; current opt-in real OCR tests ran without skips on target.
- Parent owns STATE/ROADMAP/requirements and final independent review. No global planning or user edits were included in these commits.

## Self-Check: PASSED

Verified both tool files, contract tests, report, raw suites, source provenance and referenced screenshots exist; RED/GREEN/evidence commits exist and delete no tracked files. Report validation returns false with14 product gates and5 cleanup predicates true, as required by the recorded preservation limit. Summary structural checks are recorded by the executor separately.
