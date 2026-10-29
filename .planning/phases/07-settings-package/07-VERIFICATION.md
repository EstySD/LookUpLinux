---
phase: 07-settings-package
verified: 2026-10-29T04:53:22Z
status: passed
score: 6/6 must-haves accepted (5 verified, 1 scoped override)
overrides_applied: 1
acceptance: agent under explicit --auto
native_strict_accepted: false
original_preserved: false
overrides:
  - must_have: "Original powered-off VM and unrelated entries remain untouched; evidence distinguishes real login/runtime checks from mock/SSH invocation."
    reason: "Scoped workflow-continuation exception for original-VM preservation only. The original VDI byte identity failed and earlier transient GuestProperty bookkeeping is separately recorded. Logs show a separate original GUI run with unknown actor; independent disks and clone-UUID controls support separation from the product exercises, without proving cause or preservation. Fourteen product gates and unrelated-entry/data retention are independently evidenced. Keep the raw strict report false, do not restore/overwrite original data or claim preservation, and carry the unresolved limit forward."
    accepted_by: "gsd-verifier agent, exercising the user's explicit --auto delegation to accept nonblocking verification limits"
    accepted_at: 2026-10-29T04:53:22Z
---

# Phase 7 Verification

**Goal:** Native settings affect the running application, login starts it according to configuration, Arch installation works through PKGBUILD, and a Russian guide/read-only diagnostic are available.

**Disposition:** Product goal achieved. Canonical workflow status is **passed with one explicit agent exception**. This is not a clean native-harness pass: `07-native-report.json` remains `passed:false`, with 14/14 product gates and 5/6 cleanup predicates. Original VM preservation remains failed, not verified. No human acceptance is recorded.

## Observable Truths

| # | Must-have | Status | Code and observed evidence |
|---|---|---|---|
| 1 | SC1 / SET-01: effective native shortcut, dictionary enabled/order, timeout, online and autostart settings | VERIFIED | Settings tray opens one reusable native window. Atomic config merge retains unrelated values/IDs; off-GUI transaction waits for matching worker reload acknowledgement. Installed physical D -> E change: old D stopped; E triggered. Actual reorder/disable changes next articles; offline policy leaves oracle attempts 1 -> 1; configured 2-second timer hides after 2.073s. Held old lookup is invalidated without reusing generations. |
| 2 | SC2 / TRIG-04: actual login follows enabled/disabled checkbox | VERIFIED | CLI tests saved flag before Qt; supported XDG entry uses installed absolute --autostart command. Actual SDDM Wayland session22 remains ownerless for 12.143s with flag false. Session48 starts singleton installed --autostart PID2418 for 13.791s after flag true. Both observers explicitly never launch the product; session1 additionally records initial enabled startup PID695. |
| 3 | SC3 / INST-01: makepkg install provides dependencies/Mueller/helper/launcher/working key and capture; pacman removal removes owned files/registration | VERIFIED | Actual makepkg -si exit0, pinned private kdotool with no missing linkage, installed system Mueller, valid desktop identity and authorized ScreenShot2/OCR from physical key. Pacman removal has zero package files/actions/keys before manual refresh; physical E produces no mutation and unrelated U still works. Config/history/cards/unrelated desktop hashes are unchanged. Loaded daemon survives removal until actual tray Exit, accurately documented; removal is not claimed to kill loaded code. |
| 4 | SC4 / INST-02: Russian installation/manual KDE shortcut guide and useful read-only doctor | VERIFIED | README gives staging then makepkg, current KDE shortcut UI, dictionary paths/settings, autostart, doctor, Quit/removal/data retention and limits. Installed doctor healthy/offline cases exit0; missing tools/damaged dictionary exit1 with actionable Russian output. All four profile inventories remain unchanged and profiles are removed. Code performs no history lookup, network, clipboard read or capture. |
| 5 | User D-11: visible actual dictionary destination, native folder open and unchanged-field Apply rescan without restart | VERIFIED | Selectable resolved path and local-file QDesktopServices URL; explicit click creates the destination. Native Dolphin confirms the displayed URL open. Complete StarDict sets copied into subfolders appear after acknowledged Apply in the same Engine and serve the next query. Empty/invalid-root and native-open failures preserve other settings and fixed readable status, with dedicated regressions. |
| 6 | Plan05: original VM untouched; unrelated entries preserved; real and controlled evidence distinguished | **PASSED (override), original-preservation portion only** | Original byte identity failed. Scoped agent exception above permits product workflow continuation; it does not turn the raw preservation predicate true. Unrelated entries/hashes/physical U and the separation of actual physical/login/remove checks from controlled policy/error oracles are independently verified. |

**Score:** five truths verified, one accepted through a scoped override. All four roadmap product criteria and four requirement IDs are satisfied; the additional plan preservation truth is not falsely certified.

## Artifact, Wiring and Data-Flow Checks

| Artifact | Substantive implementation and wiring |
|---|---|
| `lookup/config.py` | Compatible per-field loading and bounded atomic merge/write; real config drives startup and reload. Unavailable dictionary IDs and unrelated keys are retained; rollback can restore the exact old ID set. |
| `lookup/app.py` | Existing worker closes/reopens its own resources through ExitStack, acknowledges explicit revisions and invalidates old generation work. Lookup, history and learning snapshots retain previous cancellation/data contracts. |
| `lookup/lifecycle.py`, `lookup/platform.py` | Fixed owned KDE _launch identity; conflict preflight, actual key mutation/readback and rollback. Source/package entries avoid shadowing; centralized installed helper resolver uses private path. |
| `lookup/settings_gui.py`, `lookup/gui.py` | Native fields, scroll/keyboard controls, plain copyable path, native folder open and serial asynchronous Apply. Exact reload revision gates success; pending Close remains usable; next popup takes acknowledged timeout. |
| `PKGBUILD`, `packaging/*`, `tools/stage_package.py` | Deterministic bounded source staging, pinned upstream SHA values, official dependencies, private helper and Mueller files, absolute wrapper/desktop/autostart and capture metadata. Real package build/install/removal evidence, not file existence alone. |
| `lookup/doctor.py`, CLI, README | Doctor routes before application/history work; bounded subprocess dictionary readers bypass cache writers, tools/session/actual binding are inspected without lookup/network/capture. Russian guide covers the supported lifecycle and real limits. |
| Native harnesses/tests/evidence | Clone UUID/MAC/port guards on physical controls, actual installed/graphical-login/removal observations, explicit controlled seams and strict false-on-missing/failed gates. The failed original predicate was retained. |

Key links traced: Settings -> config/key transaction -> Engine revision -> new dictionaries/online policy -> popup timeout; XDG startup -> --autostart flag -> installed Owner; package desktop -> owned actual key -> absolute installed wrapper -> authorized capture/private helper; removal -> absent system entry -> automatic registry disappearance; doctor -> read-only readers/session inspection. No orphaned/stub production path was found.

## Independent Verification

- Fresh command: `python -m unittest tests.test_config tests.test_settings_gui tests.test_lifecycle tests.test_doctor tests.test_package tests.test_check_settings_app tests.test_app tests.test_app_gui` — **114 tests OK, zero skips**, 3.271s.
- Independent JSON assertions checked 14 true product gates while strict report remains false; exactly the original cleanup predicate remains false.
- Checked enabled/disabled login samples, distinct actual SDDM sessions, installed argv/PID stability, observation duration and no observer-started product.
- Checked removal before manual refresh, after physical input and after tray Exit: no files/actions/keys; matching config/database/unrelated hashes; unrelated physical marker advances; loaded owner remains until Quit, then disappears.
- Checked actual doctor exits, unchanged profile inventories and cleanup; source archive provenance and installed settings source hash match final local LF-normalized production source.
- Verified commit difference from physical capture proof `17b3b22` to final product `a48fce1`: only Settings empty-root handling/test and its summary changed. Capture/lifecycle/helper authorization implementation is unchanged.
- Independently inspected light and DPR1.5 dark native Settings images. Controls/path/list are readable; scrolling and persistent Apply/Close remain accessible.
- Inspected full logs: host **701 tests OK, eight known target-only skips**, 30.036s; target **701 OK, zero skips**, 36.974s. Existing negative-deadline SemLock diagnostic is retained rather than hidden; positive writers passed.

The raw native report SHA-256 at verification is `33294577ee047e26e3f70032ba2d712741c94d75d1fefd98d8b50e54019925c7`. This verification does not edit that report.

## Requirements

| Requirement | Plans | Result |
|---|---|---|
| SET-01 | 01,02,03,05 | SATISFIED — actual effective native settings and acknowledged reload. |
| TRIG-04 | 01,02,04,05 | SATISFIED — real enabled/disabled SDDM login, not merely command simulation. |
| INST-01 | 02,04,05 | SATISFIED — real package/helper/Mueller/authorized capture/key/install/remove and retained user data. |
| INST-02 | 04,05 | SATISFIED — Russian fresh-reader guide/manual KDE steps and read-only actionable doctor. |

No Phase7 requirement is orphaned. D-11 is additionally verified as an explicit user clarification.

## Preservation Exception: Facts That Remain Unresolved

The original `arch-kde` disk grew from **9848390144** to **9958490624** bytes. Baseline SHA-256 `9f2b4a34fe8ae0f73db8df281f9414a68c9e9483e3d981b7a288f53c5b18fd1c` differs from independently checked final `fd3c5382d73a5ebdf849c5abe2e974c227398b1389b5738d5729714aa9c401b1`.

Recorded original logs show a separate VirtualBoxVM.exe GUI run around 2026-10-28 15:55–16:11 UTC. Its actor is **unknown**. Separate disk UUIDs and clone-targeted workflow controls do not prove the original unchanged or establish who caused that run. Earlier automatic removal of thirteen transient original GuestProperties during preparation is a separately disclosed metadata change, not an explanation for the later disk hash difference.

No original restoration, rollback, deletion or compensating write is claimed or authorized by this exception. Both machines end powered off; the clone is retained for review. The exception is justified only for continuing independently verified product work under the user's explicit --auto preference for nonblocking limits. It does not waive a product requirement, certify every plan safety assertion, attribute the unknown actor, or make strict native acceptance pass.

## Other Limits and Disconfirmation

- A mock key/login test would not establish the contract; actual physical old/new-key and separate SDDM sessions were inspected. Controlled network and failure oracles are used only for policy/error behavior, never described as live-provider success.
- Package removal can leave already-loaded code in memory. Actual registry/key/file removal and eventual tray Quit are separately evidenced, and README explicitly requires Quit before uninstall.
- Native app screenshots are not games or performance measurements. Clean-snapshot reliability, real fullscreen games, sustained load and latency distribution remain Phase8.
- Project license remains unspecified; Mueller's upstream GPL wording lacks an exact version. Included notices preserve that uncertainty; local package success is not redistribution/legal clearance. Prior public-provider HTTP429 remains a handled availability limit.
- No open product/code blocker was found. Agent acceptance under --auto is explicit; no human test or human acceptance is fabricated. The operational preservation failure remains visible through the scoped override and strict false report.
