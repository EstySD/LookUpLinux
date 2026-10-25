---
phase: 02-offline-dicts-translate
plan: 11
subsystem: verification
tags: [archvm, mueller, timing, urllib]
requires:
  - phase: 02-offline-dicts-translate
    provides: complete CLI and dictionary/translation libraries
provides:
  - Three-interpreter test results and live Mueller/network evidence
  - D-09 timings and independent-provider decision
affects: [03, 05, 07, 08]
tech-stack:
  added: []
  patterns: [isolated UAT databases, committed VM archive]
key-files:
  created: [.planning/phases/02-offline-dicts-translate/02-VM-RESULTS.md]
  modified: []
key-decisions:
  - Preserve the existing VM checkout and test an isolated committed archive.
  - Retain MyMemory for phrases/sentences; all Google clients currently work from this VM.
  - Real MDX/DSL compatibility remains explicitly unverified under D-34.
requirements-completed: [TRAN-01, TRAN-02, TRAN-03, TRAN-04, TRAN-05, DATA-03]
duration: 15min
completed: 2026-10-25
status: complete
coverage:
  - id: D1
    description: Windows 3.14/3.12 and Arch 3.14.8 full suites
    verification:
      - kind: integration
        ref: 02-VM-RESULTS.md#test-suites
        status: pass
    human_judgment: false
  - id: D2
    description: Real Mueller lookup, timing, network/cache/phrase behavior and failure deadlines
    verification:
      - kind: integration
        ref: 02-VM-RESULTS.md#mueller-7-checks
        status: pass
      - kind: integration
        ref: 02-VM-RESULTS.md#online-from-the-vm-sc4
        status: pass
    human_judgment: false
---

# Phase 2 Plan 11: VM Verification

All 482 tests passed on both Windows interpreters (6 skips each) and Arch
Python 3.14.8 (2 skips). Both real Mueller sample tests then passed without
skips in the VM. Its 46231 valid entries and one skipped entry match the
reader fixtures. All planned exact/base-form queries behaved as specified.

Mueller open median/max was 91.0515/110.784 ms and search median/max was
4.8395/7.708 ms, within 300/20 ms targets. Google gtx, dict-chrome-ex, at and
MyMemory all answered via application urllib. Cache hits used zero network
time; unknown words and sentences did not create word rows; a phrase did.
Refused proxy failures preserved dictionary output, and blackhole calls
returned in 3.195/3.176 seconds including interpreter and dictionary startup.

## Deviations and Remaining Limits

Used `~/LookUpLinux-gsd-e92a26a` to preserve existing VM contents. Temporary
database/cache/config roots were automatically removed. No packages installed.
Mueller data was copied only to the VM's dictionary directory, never Git.

Real MDX: unverified (no file supplied). Real DSL: unverified (no file supplied).
As D-34 allows, these remain Phase 8/user-dictionary checks rather than failures.
Provide a real MDX (ideally LZO or Encrypted=2) and optionally DSL in the VM's
`~/.local/share/lookup/dicts/` to verify their real-world compatibility.

## Next

All eleven Phase 2 plans have summaries. Ready for phase verification and UAT.
