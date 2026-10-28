---
phase: 07-settings-package
plan: 04
subsystem: package-doctor-docs
tags:
  - arch
  - package
  - readonly-diagnostics
requires:
  - phase: 07-02
    provides: Owned lifecycle, installed paths and private helper resolution
provides:
  - Deterministic restricted local source staging and checksum-pinned Arch package
  - Read-only bounded doctor CLI and Russian installation guide
affects:
  - 07-05
  - 08-vm-hardening
tech-stack:
  added: []
  patterns:
    - Explicit diagnostic stream and finite readonly child parsing
    - LF-normalized deterministic source archive with recorded hashes
key-files:
  created:
    - PKGBUILD
    - tools/stage_package.py
    - lookup/doctor.py
    - tests/test_package.py
    - tests/test_doctor.py
    - packaging/lookup
    - packaging/org.lookup.Linux.desktop
    - packaging/org.lookup.Linux.autostart.desktop
    - packaging/THIRD-PARTY.md
    - README.md
  modified:
    - lookup/__main__.py
key-decisions:
  - Use an ordinary local package with official dependencies and a private pinned helper; no AUR prerequisite.
  - Keep the project license and precise Mueller GPL version explicitly unresolved.
  - Never call cache-writing DSL/MDX factories during doctor diagnostics.
  - Installed/login/capture/removal acceptance and the final D-11 snapshot remain plan 05.
requirements-completed: []
duration: unmeasured
completed: 2026-10-28
---

# Phase 7 Plan 04: Package, Doctor and Russian Guide

**The local Arch package builds with verified upstream assets, and the doctor checks tools, dictionary indices and session registration without lookup side effects.**

Implementation: `tools/stage_package.py` and `lookup/doctor.py`.

## Delivered Interfaces

- `python tools/stage_package.py --output EMPTY_DIRECTORY` creates `lookup-source.tar.gz`, a ready `PKGBUILD` and `SOURCE.json`. It refuses a nonempty/symlink destination and unsafe source links. Only application Python/data and explicit package entries/attribution are included. Sorted USTAR entries have fixed ownership/time; text is normalized to LF so Windows checkouts preserve Linux shebangs. The manifest records archive/recipe/upstream hashes and included filenames.
- Package name is `lookup-linux`, local version `0.1.0-1`, x86_64. The launcher is `/usr/bin/lookup`, application `/usr/lib/lookup/app/lookup`, helper `/usr/lib/lookup/kdotool`, and Mueller `/usr/share/lookup/dicts/mueller7`. The wrapper imports independently of checkout cwd/PYTHONPATH. All runtime dependencies are official packages; `package()` performs no download.
- Official kdotool 0.3.0 archive SHA256 is `2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff`. Mueller archive SHA256 is `1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed`. `!strip`/`!debug` preserve the prestripped helper and avoid an unwanted debug package. Its Apache-2.0 license and WordNet notice are retained. Only the three required Mueller files are packaged; redundant data/swap files are excluded.
- The installed desktop uses `/usr/bin/lookup --trigger`, owned app identity, default shortcut and `X-KDE-DBUS-Restricted-Interfaces=org.kde.KWin.ScreenShot2`. System autostart uses `/usr/bin/lookup --autostart`, `TryExec` and `OnlyShowIn=KDE`. It creates no installed user shadow. Real authorization, login and unregister behavior remain plan 05 checks.
- `doctor.check()` returns immutable `Diagnostic(code, ok, message)` records; `doctor.run(stream)` requires the caller's explicit output stream and returns 0/1. The lazy mutually exclusive CLI supplies stdout. No implicit library printing/logging was added.
- Tool probes are finite; the existing private-helper resolver is used. kdotool receives the discovered session environment even for its version probe, with `v0.3.0` handled correctly. Service calls use a 1200 ms timeout and read-only actual shortcut inspection.
- Dictionary discovery and pure index parsing share one isolated child process with an eight-second deadline. StarDict is opened read-only; DSL/MDX use existing pure parsing helpers and bypass their cache-writing factories. Diagnostics omit headwords, dictionary titles and personal paths. Disabled, missing, damaged, unsupported and timed-out sources have fixed actionable states. No history/card DB, clipboard, screenshot, network probe or GUI application is opened.
- Russian README covers build/install/start, actual settings/shortcut behavior, source versus installed use, doctor exit status, autostart, dictionary paths, review/export, uninstall/data retention and known limitations. Its D-11 paragraph documents the copyable actual folder, «Открыть папку словарей», complete files/subdirectories and «Применить настройки» rescan flow. A cold read corrected an extra `cd` and foreground startup sequencing.

## Validation Results

- Package/lifecycle/platform task suite: **29 tests OK**, exit 0.
- Final affected package/doctor/CLI/core-import/privacy suite: **29 tests OK**, 3.388s, exit 0. This includes the final session-environment/version regression and Windows-CRLF staging regression.
- Shared host full suite from the GUI executor: **692 tests OK, 8 skipped**, 26.499s. That baseline preceded the final added doctor version regression; final affected host checks above cover the subsequent narrow changes. Broad host repetition was intentionally avoided per parent coordination.
- Final owned clone full suite: **693 tests OK, zero skips**, 35.680s, exit 0, using `QT_QPA_PLATFORM=offscreen LOOKUP_TEST_OCR=1 LOOKUP_TEST_DICTS=/home/arch/.local/share/lookup/dicts`. It includes the final doctor/package changes and the existing OCR/Mueller/learning regressions. Output is retained at the host temporary file `lookup-package-07-final-tests.txt`, SHA256 `71496cd7e16e507ad7e1e4d0e5841e42286c133c946db1a9f51b733fa794a59b`.
- Actual ordinary-user `makepkg --noconfirm` in the owned clone passed dependency checks, all three source hashes, package creation and packaging checks. No package installation was performed. `desktop-file-validate` passed for both staged installed entries.
- `ldd` on the private helper resolved libdbus, libgcc, libc, libsystemd and the loader with no missing library. The packaged helper bytes match the extracted pinned helper exactly.
- Final source/package archive inspection confirms settings_gui, doctor, application data, licenses, both desktop entries, private helper and only `.ifo/.idx.gz/.dict.dz` Mueller data. Tests, planning files, database/cache files and swap data are absent.
- Actual readonly doctor probe in a temporary isolated XDG/LOOKUP profile reported tools and Mueller **46231 entries / 1 skipped** successfully. It correctly returned **1** for the clone's not-yet-registered application key. **Zero files were created**, and **PyQt6.QtWidgets was not loaded**. No entry registration or live session mutation was attempted.
- Whitespace checks on owned sources/tests: exit 0. No history, private query or raw provider response is emitted by the doctor.

## Package Handoff to Plan 05

Only `lookup-gsd-07` was used through SSH port 2227; original `arch-kde` stayed off.

Validated build directory: `/home/arch/lookup-package-07-ready`.

- Source archive SHA256: `eaf8f72d558e94e488435d30841c8f900900fc361204c043e3153d9bf8a4e206`.
- Built file: `/home/arch/lookup-package-07-ready/lookup-linux-0.1.0-1-x86_64.pkg.tar.zst`.
- Package SHA256: `e132e44e90ac3cd7fe039a5c9f1a08fce6e584d08a00e95d7342de32fbd028fd`.
- Staged checkout: `/home/arch/LookUpLinux-gsd-package-07`; manifest: build directory `SOURCE.json`.

**This snapshot includes the completed initial Settings implementation but predates the D-11 folder-button GUI follow-up.** Plan 05 must copy the final source and stage a fresh empty build directory after that follow-up, then run the actual README `makepkg -si` flow. These pre-install build hashes are not final installed acceptance evidence.

## Commits

1. Task 1 RED: `da6920a` — package/source/installed identity contracts.
2. Task 1 GREEN: `fad5222`; follow-up `8838b96` — package, deterministic staging, pinned helper/data, LF handling and prebuilt-byte preservation.
3. Task 2 RED: `2e2852d` — readonly diagnostics and forbidden-effect contracts.
4. Task 2 GREEN: `d850595` — bounded doctor and lazy CLI dispatch.
5. Task 3: `20f2fb5`, `5aaa330` — Russian guide and explicit D-11 dictionary-folder flow.

## Deviations and Limits

- The first build revealed Arch's default debug/strip processing of an already-stripped upstream executable. The recipe now explicitly disables both; the final build has no extra debug package or missing-symbol warning.
- A real SSH doctor probe exposed kdotool's KDE_SESSION_VERSION requirement before even handling `--version`, plus its `v` prefix. The existing session resolver is now passed to the probe; a regression covers that exact format. This changes no graphical session state.
- QStarDict labels the pinned Mueller archive GPL but ships no license text/version. The primary SUSE distribution metadata labels its Mueller package GPL-2.0+, which does not establish the exact grant for this different pinned archive. The package therefore records GPL-version-unspecified attribution and the project's own license as unspecified, without inventing redistribution clearance. This is a local-build package; redistribution licensing remains unresolved.
- Installed imports/helper/Mueller discovery, actual authorized capture, physical keys, real login/autostart, package removal and data preservation are mandatory plan 05 checks. No complete Phase 7 requirement or human acceptance is claimed here.
- D-11 GUI/native folder acceptance is a coordinated follow-up, not silently included in the recorded build/full-suite snapshot. The README already describes the approved flow.
- Existing target SemLock teardown tracebacks belong to the deliberately negative-deadline concurrency test previously diagnosed in Phase 5.1; the final runner has zero failures/errors. The shared host baseline retains eight known platform/environment/opt-in skips; final target tests execute those gates.
- No user metadata, global planning state, lifecycle/platform implementation or another agent's GUI files were committed by this unit. No known stub prevents its package/doctor/doc contract.

## Self-Check: PASSED

Owned implementation/test/package/doc files and this summary exist. All seven listed task commits exist. Final focused checks, full target checks, actual build, installed-file metadata and readonly side-effect probe passed within their stated scope. Parent owns final independent phase verification and state/requirement updates.
