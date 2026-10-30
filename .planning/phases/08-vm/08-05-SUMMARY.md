---
phase: 08-vm
plan: 05
subsystem: clean-install-and-final-evidence
tags: [arch, sddm, package, preservation, strict-aggregate]
requires:
  - phase: 08-02
    provides: Raw performance, stability, privacy, scale and fault evidence
  - phase: 08-03
    provides: Actual fullscreen Wesnoth routes
  - phase: 08-04
    provides: Retained mandatory captured-game verification gap
provides:
  - Separate clean graphical app-profile baseline and real README install/login/removal cycle
  - Raw-backed seven-criterion aggregation and scoped final cleanup validation
  - Explicit open GAME-01 gate for subsequent focused gap closure
affects: [phase-verification, GAME-01-gap-closure]
tech-stack:
  added: []
  patterns: [ordered login observations, exact retention hashes, raw cleanup aggregation]
key-files:
  created:
    - tools/check_hardening_install.py
    - tests/test_hardening_install.py
    - .planning/phases/08-vm/08-install-native-report.json
    - .planning/phases/08-vm/08-final-aggregate.json
  modified:
    - tools/check_hardening.py
    - tests/test_hardening.py
key-decisions:
  - A new owned graphical account establishes a clean app/profile baseline, not pristine Arch.
  - Genuine enabled and disabled login observations cannot launch the product or reuse an old owner.
  - Automatic removal observation precedes any explicit registry refresh.
  - The mandatory captured-game gap keeps phase acceptance false despite successful independent installation gates.
requirements-completed: []
status: executed-with-verification-gap
duration: approximately 35min
completed: 2026-10-30
---

# Phase 8 Plan 05: Clean Install and Final Evidence Summary

**A separate clean graphical profile passed actual local installation, physical OCR, enabled/disabled SDDM login and data-preserving removal; final phase acceptance remains false because useful captured-game proof is missing.**

Implementation: `tools/check_hardening_install.py` and `tools/check_hardening.py`.
Principal commits: 11d2bc5 (install RED), 884933a (install GREEN), 0d6f91e (aggregate RED), 24716f7 (sustained login/aggregate), 6ebf81c (raw build proof), d5488b3 (global cleanup).

## Validation Results

Authoritative installation result: `08-install-native-report.json`: **11/11 product gates and 7/7 installation cleanup checks true, native passed:true**. Final seven-group result: `08-final-aggregate.json`: **6/7 groups and 11/11 global cleanup checks true, overall passed:false**. The latter recomputes raw performance, resource, scale, privacy/fault, install, game and meaning records. It does not promote prior summary booleans or alter the historical phase07 report. The two-game group remains false because plan04 has zero accepted useful captured routes. Independent final code/security review and verifier are parent-owned, explicitly pending in the aggregate; this summary does not claim milestone completion or human acceptance.

| Independent installation observation | Actual result |
| --- | --- |
| Clean baseline | New lookup08install UID1002; genuine SDDM Wayland session21; product absent, no product user config/data/cache/dictionary/desktop shadow, ownerfalse, keys[] |
| README commands | Existing official dependencies inventoried; ordinary arch build user ran stage_package.py then actual makepkg-si; exit0, no AUR/pip workaround |
| Installed identity | Absolute installed command from /tmp without PYTHONPATH, private helper and system Mueller; exact desktop ScreenShot2 permission/Exec identity recorded |
| Physical lookup | PRIMARY absent, actual Meta+Shift+D over observed bank coordinates506,393, plain installed owner4163; useful Mueller article visible and bank count1 persisted |
| Enabled login | Previous owner quit via tray; new genuine session66 launched only installed --autostart PID4929 after session start; stable observation for over12s |
| Disabled login | Preference saved false, owner quit; genuine session90 remained ownerless throughout over12s of actual observations |
| Removal | Actual pacman-R exit0 with daemon already stopped, all package/helper/dictionary/desktop files removed |
| Registry/key | Immediate post-remove snapshot briefly retained D; later automatic observation cleared it before physical D and before manual refresh; physical D left ownerfalse and DB unchanged |
| Unrelated/data | Physical U advanced its marker; config/DB/unrelated desktop SHA256s and seeded history/card rows remained identical across removal |
| Explicit refresh | Supported kbuildsycoca6 ran afterward, exit0, keys remained absent; not substituted for the earlier automatic outcome |

Actual install source archive SHA and package SHA are recorded in `08-install-build-provenance.json`. The compressed source archive differs from the benchmark archive, but a read-only comparison proves **all32 source member names and bytes identical** (`08-install-source-comparison.json`). Production code remained unchanged; no performance or game run was silently relabeled.

Fresh focused verification after the final raw-binding correction: **50 tests passed**. Final host discovery at a10c5e1: **752 tests OK, 8 skips, 31.220s, Python exit0**. Last target discovery at d5488b3, before the host-only raw-binding correction: **751 tests OK, zero skips, 40.223s, Python exit0**. Details are retained in `08-install-host-tests.txt`, `08-install-target-tests.txt` and `08-install-final-suites.json`. Target used actual image OCR and `/home/arch/lookup-readme-08-build/src/mueller7`, a retained verified real Mueller directory after product removal; the application was not reinstalled to make tests pass. Preliminary pre-freeze suite logs remain separate. Existing forced-deadline multiprocessing SemLock teardown noise is preserved in target output; actual assertion/exit results are recorded explicitly.

## Raw Evidence and Remaining Mandatory Gap

The aggregate retains the actual30-request median1128.057506ms/p951455.247426ms, final320-completion recursive-resource evidence, rapid burst, four scales and negative-origin unit check, privacy/fault records and live meaning denominator. Live meaning remained0/6 successful; conditional and UI success latency remain null, with provider-only origin explicit. Optional second output/borderless remain unverified.

Wesnoth's two real fullscreen routes remain valid. Freedoom's real fullscreen/lock/camera observations do not supply a successful useful captured lookup. Therefore GAME-01 remains open and **overall passed:false**. This exact gap needs subsequent targeted work; neither an ungrabbed game nor a broad historical exception waives it.

## Deviations and Corrections

- **[Rule 1 - Harness]** Initial retention card seed used a token containing digits, which the real learning API rejected. Corrected to the valid publicseed token; the unsuccessful seed row was retained, not erased to manufacture a clean baseline. Baseline inventory preceded all seeding.
- **[Rule 3 - Environment]** Protected KWin environ prevented direct socket discovery. The helper selected the single actual UID-owned Wayland socket and used the production session environment for KDE helper calls. Initial helper GUI probes without that environment aborted; no product failure was inferred.
- **[Rule 1 - Observation]** Initial fixture coordinates preceded compositor placement and selected blank space. The rejected pilot remains; accepted physical input used the actual fresh observed bank position. The product daemon was plain installed code, not an injected observer.
- **[Rule 1 - Reviewer corrections]** RED tests reproduced empty installed/retention/cleanup proofs, swapped login roles, empty/reversed/short observation samples, multiple/stale/disappearing owners and missing global cleanup. Final validators require exact installed paths/hashes, retention schema, expected login roles, at least10s of ordered actual samples with a stable new singleton, required cleanup names and all scoped raw cleanup records. Pure oracle fixes reused adequate actual native evidence; they did not rerun or falsify game outcomes.

## Cleanup and Preservation

The original SDDM configuration files were preserved byte for byte. Only the new explicitly owned override was removed after exact-content verification. The separate account and synthetic seeded profile are retained for independent review; existing lookup07 data was not erased. No snapshot or rollback was needed. The original VM was never booted, reverted, deleted or written by this unit. Its historical phase07 unknown-actor disk exception remains exact and separate.

Final cleanup observations are recorded in `08-install-cleanup-final.json`. Final aggregate cleanup derives named observer/game/helper, activation/environment, network/dictionary/layout, input/clipboard and both-VM-off checks from the actual02/03/04/05 cleanup records. Missing, false and unknown-only cleanup cannot pass.

Both VMs are verified powered off. The clone's prior bidirectional shared clipboard was restored only after poweroff;3D remained at its prior enabled setting throughout this installation unit. No network/filter or scale changes were made. Local packaging does not resolve the project's unspecified own license or Mueller's imprecise GPL attribution and is not redistribution clearance.

## TDD Gate Compliance

Install RED11d2bc5 precedes GREEN884933a. Subsequent reviewer RED a723712/68c0542/296dc3f and raw-build REDbb62550 precede their corrections. Aggregate RED0d6f91e and global-cleanup RED322b65c precede GREEN24716f7/d5488b3. No production placeholder or fabricated native success was introduced.

## Final Raw-Binding Follow-up

Canonical review found the assembler regenerated build exits/package hash and negative-origin exit/count instead of consuming their saved outcomes. RED49e6659 reproduced six false passes; GREENa10c5e1 now reads saved build provenance, requires its source hash to match SOURCE, validates the actual build-log digest/success markers and preserves the recorded package hash. The negative-origin check consumes a fresh observed subprocess result and validates count/test identity/success against its bound log. Failure logs still reject when their digest is recomputed to match, preventing a checksum-only false pass.

Fresh focused verification after this correction: **50 tests passed**, including the six assembly mutations. Actual native installation/removal observations remain unchanged and the regenerated native report remains true; mandatory captured-game and overall phase acceptance remain false. The prior target run is explicitly labeled **751 tests at d5488b3, before this host-only correction**. The clone was not booted to relabel that result; a final target rerun belongs to later native gap work after all source changes settle. The original negative-origin PowerShell capture is retained beside the fresh structured result and log.

Independent canonical review cleared this correction after fresh focused reproduction; no open code-review finding remains. Parent-owned final verifier and mandatory captured-game gap closure still follow separately.

## Self-Check: PASSED

Implementation files, task commits, actual baseline/install/login/removal records and suite artifacts exist. The parent owns global state and requirement transitions.
