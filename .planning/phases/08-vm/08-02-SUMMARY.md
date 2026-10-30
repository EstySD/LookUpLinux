---
phase: 08-vm
plan: 02
subsystem: native-hardening
tags: [kde, wayland, physical-input, performance, privacy, recovery]
requires:
  - phase: 08-01
    provides: Numeric production timing and predeclared strict evidence oracles
provides:
  - Installed physical30 latency and recursive320 completion/resource evidence
  - Actual rapid burst, four-scale, clipboard and three-fault acceptance
  - Guarded clone controls and retained rejected native attempts
affects: [08-03, 08-04, 08-05]
tech-stack:
  added: [test-only tesseract-data-rus]
  patterns: [kernel monotonic input, optical current-content checks, atomic evidence, recursive process identity]
key-files:
  created:
    - tools/check_hardening_vm.ps1
    - .planning/phases/08-vm/08-native-final-report.json
    - .planning/phases/08-vm/08-stability-recursive-final-attempts.json
  modified:
    - tools/check_hardening.py
    - tests/test_hardening.py
key-decisions:
  - Acceptance starts at the verified kernel event and ends at actual useful-frame capture; receipt and internal show are not visibility.
  - All measured attempts and rejected observer/setup batches remain available; only final named workloads supply acceptance.
  - Resource checks enumerate all threads and recursive descendants and reject unreadable or changed identity.
  - Zero live meaning successes leaves conditional and UI latency null; provider availability does not replace article timing.
requirements-completed: [PERF-01]
duration: approximately 14h including quota pauses
completed: 2026-10-30
---

# Phase 8 Plan 02: Installed Native Hardening Summary

**Installed physical lookups passed a 1128ms median, 320 sustained completions, rapid burst, four actual scales, privacy and fault recovery in the owned clone.**

Implementation: `tools/check_hardening.py` and `tools/check_hardening_vm.ps1`.
Principal implementation commits: 52ea03f, a3c887f, 2f479d3. Evidence commit: 74df213.

## Validation Results

Agent acceptance is recorded in `08-native-final-report.json`: **6/6 required product groups and 12/12 cleanup checks passed**. This is automated agent acceptance, not human testing. Game/fullscreen acceptance belongs to the following serialized plans.

| Final workload | Actual result | Evidence |
| --- | --- | --- |
| Physical latency | Exactly30 successful requests; median1128.057506ms, nearest-rank p951455.247426ms | `08-performance-final-attempts.json`, corresponding report |
| Cold/distinct/repeat | 3 cold median1455.247426ms;18 actual distinct Mueller words median1112.8134355ms;9 repeats median1128.711958ms | Same raw30; subgroup p95 retained |
| Sustained | 20 warmups +320 completions, unchanged PID/start/run,32 resource observations | `08-stability-recursive-final-attempts.json` |
| Resources | Early RSS174657536; late174698496; cooldown174702592 bytes; late trend8192 bytes | Corresponding stability report |
| Idle/counts | 5.200s cooldown;9 threads/22 FDs; recursive descendants empty; history delta320, enrichment extra0, integrityok | Same raw resources/cooldown/history |
| Rapid burst | 10 complete physical chords, actual kernel gaps28.273–83.119ms;1 accepted newest completion; history+1; subsequent lookup responsive | `08-burst-final-verified.json` and PNG/report |
| Scaling | Actual100/125/150/200%; correct cursor/selected word, first useful popup within work area; original scale restored | `08-scales-final-verified.json`, strict complete report and four `08-scale-*.png` images |
| Privacy | Exact PRIMARY/CLIPBOARD/ordered Klipper hashes unchanged through burst/scales/stress and subsequent faults; no production PNG in temporary/runtime/DB directories | `08-privacy-final-report.json`, `08-privacy-after-faults.json` |
| Faults | Real network outage, real owned dictionary unavailable+acknowledged reload, explicitly injected ScreenShot2 transport failure; all three recovered | `08-faults-final-report.json` and per-fault frames/raw reports |

The fixed resource allowances were not relaxed. A late stress sample1793.945ms remains in the raw record; the main30 median gate is a separate fixed workload. Maximum main capture uncertainty1497.571379ms is retained rather than subtracted.

Final full host suite: **730 tests,8 existing host skips,30.732s, Python exit0** (`08-final-all-source-host-tests.txt`). Final target suite: **730 tests,0 skips,38.857s, exit0**, with `LOOKUP_TEST_OCR=1` and real `LOOKUP_TEST_DICTS=/usr/share/lookup/dicts/mueller7` (`08-final-verified-target-tests.txt`). The target covers actual OCR, both real Mueller tests and the POSIX cases skipped on Windows. Final focused checks after cleanup tooling:73 tests passed.

The target log deliberately retains3 child `SemLock._rebuild` FileNotFoundError traces, consistent with the previously identified forced-deadline teardown in `test_reader_loop_has_deadline`; the top-level suite exited0. Host stderr projection appears as PowerShell NativeCommandError/RemoteException, while the actual Python exit was0. Neither log is described as warning-free.

## Actual Runtime and Measurement Contract

The full owned clone is `lookup-gsd-07`, UUID `cf207909-94b5-4b49-8bd8-ccff973c1dc8`, independent disk UUID `2712d710-daaa-449c-843d-d570091127bc`, SSH2227. The original VM was never booted, reverted or written by this harness. Physical controls check clone name/UUID/attachment and original-off state. The owned account is lookup07, UID1001, HOME `/home/lookup07`, in a genuine SDDM Wayland session.

Final installed production source is **5d04a4c**, source archive SHA256 `5451493544c90376700aea542ceb91357509658304382f65d36ac8455b1ddf85`, actual makepkg-si package SHA256 `17dd294e0aacda94a4e80380d0a00bbbc7b9f0cdadbd96ba1538f528f9b11fa5`. Source provenance and pinned package inputs are embedded in the final report. The executable is installed `/usr/bin/lookup`, independent of checkout cwd; ScreenShot2, English production OCR and real system Mueller were used.

The observer discovers the AT keyboard from sysfs, sets EVIOCSCLOCKID(CLOCK_MONOTONIC), and records the configured chord's completing kernel key event and release without grabbing input or logging other keys. Verified kernel event time and actual ScreenShot2 useful-frame capture end share guest CLOCK_MONOTONIC. Receipt is diagnostic only. Optical checks require the current leading word, Mueller identification and canonical article body; burst also verifies the actual final count. Internal present alone cannot pass.

Cold samples prove owner absence before the physical shortcut and a new process born after input. The clean owned Plasma session exports timing/profile variables; installed desktop Exec stays `/usr/bin/lookup --trigger`, with no user desktop shadow. Actual cold CLI/client/owner startup is included. Timing records were collected from the owned journal by numeric prefix and actual PID/run; no unrelated journal content was published.

Final sustained identity was PID27115, process start172467, run1386999639202549. Recursive observations validate UID/start before and after traversal of every task's children. Missing metadata, identity reuse, changed child sets and unreadable descendants fail closed.

## Fault and Availability Details

- Network: a clone-DMI-guarded, explicitly marked nft table rejects only UID1001 IP output. Counter and actual `нет сети` frame prove the outage while SSH/Unix DBus remain usable. After deleting only the owned table, the same daemon's next physical request returned a useful article and the actual provider-blocked status. Counts1140→1141→1142, integrityok. All6 fault gates passed.
- Dictionary: an owned byte copy of real Mueller was moved outside its discovery root. Physical Settings folder/Apply acknowledged an unavailable row. A subsequent bounded not-found frame appeared within1900.864ms. Restoration and actual Apply acknowledged the dictionary; the same daemon's next physical cat lookup succeeded. Two missing attempts and recovery are all counted1143→1144→1145→1146; the initial1039ms loading-only observation is retained, not promoted to useful output.
- Capture: the test launcher explicitly replaces only installed `capture._screenshot2` in its own process and records the invocation. This is labelled injected, not a real compositor failure. Actual physical input showed the fixed capture error within1918.231ms upper bound, owner survived, history730→730, and the normal installed daemon recovered with one useful lookup/history+1. All6 gates passed.
- Live context: six bounded uncached public river/finance/repeated-occurrence/multiline probes had **0 successes/6 attempts**, reasons `blocked:6`. These are labelled provider-call-only availability probes. Conditional success median/p95 and physical UI meaning latency remain **null**. No controlled provider, cache or screenshot upload was substituted; optional cache timing has no successful live seed.

## Cleanup and Preserved Limits

Actual tray Exit stopped the product and the guarded observer stopped. Layout was restored, owned nft rules removed, the owned dictionary restored, and the exact retained default config bytes restored (SHA256 `4ab363d4620fd51d0a80f409cfc5d1ce0e636c69c87033da5d3ec23b9b67d014`). Only the exact owned Plasma environment script was removed. Test DB/cards/history and unrelated profile data were retained.

ACPI power-button shutdown did not complete within30s; controlled SSH `sudo systemctl poweroff` succeeded. **Clone and original are both powered off.** Temporary input-device access and activation environment ended with guest shutdown; the original input ACL bytes were not sampled, so byte-for-byte ACL restoration is not claimed. No unknown process was killed to simulate cleanup.

Clone shared clipboard was bidirectional at resume. It was disabled before boot and the eligible synthetic baseline, and restored to its prior mode only after shutdown. Public clipboard preparation exposed Klipper mirroring into PRIMARY; only the exact known public seed was cleared to restore the measured absent selection. Historical Klipper entries were retained; no history was cleared to obtain equality. Future native plans must isolate shared clipboard again before reading their baseline.

One output was available; second-output behavior remains unverified. Historical Phase7 preservation remains raw `passed:false` and `cleanup.original_preserved:false`, with unknown actor. Its separate GUI run and independent disks remain documented there. The final report carries that exception without rewriting it or claiming original VDI byte identity.

## Deviations from Plan

1. **[Rule1—Bug] Production cold timing and visible placement.** The orchestrator dispatched scoped production fixes1297a16 (cold child timing stderr),4ace8e9 (hold useful paint until compositor placement),5d04a4c (start inactivity timeout at actual reveal). Failed/prior-build observations remain; main30 and sustained340 were repeated on final source.
2. **[Rule1—Bug] Observer correctness.** Fixed actual Phase7 cleanup schema lookup; current-body/arm matching; reverse journal ordering; atomic result transport/read races; exact rapid cadence; all-thread recursive process ownership; and incomplete-scale false success. RED/GREEN behavioral regressions cover the defects. Review cleared the final recursive/scale corrections before the last340.
3. **[Rule3—Blocking verification] Rejected setup/batches.** Cached KDE desktop metadata caused an initial wrong-profile/no-timing startup; switched to a clean genuine session environment. A stress run stopped after10 warmups on observer metadata failure; the next contained unrecoverable handoff gaps and was controlled-stopped after267 measured rows. Atomic transport fixed the cause. A successful older build's340 is retained as historical, and the final-build incomplete resource run was stopped at20+13 before recursion was corrected. None supplies final acceptance.
4. **[Rule3—Blocking verification] Burst and privacy setup.** Slow per-input SSH bursts and an overlapping diagnostic were rejected; one retained VirtualBox COM keyboard session now supplies measured rapid chords. wl-copy inherited-channel timeout and synthetic PRIMARY interference were corrected without clearing history. Earlier baselines and diagnostics remain separate from the final eligible baseline.

## Task Commits

- Task1 RED/GREEN and matching:34f35c9,3114db8,84247e2,e3d5c9d,35632fd,52ea03f.
- Task2 cadence/fault/resource/writer corrections:7099a82,9a2ec88,cb85788,a3c887f,2f479d3.
- Retained raw evidence:74df213 (84 files, approximately5.76MB).

No production dependency or general benchmark framework was added. Test-only observer privilege is limited to the owned keyboard/profile; network mutation is UID-scoped and clone-identity guarded. No new production threat surface or unresolved functional stub was introduced.

## Self-Check: PASSED

Verified6 principal source/evidence files and all12 listed task/evidence commits exist. Recomputed final six product oracles and12 cleanup checks pass; the historical Phase7 false preservation result and unavailable live/second-output metrics remain explicit.
