---
phase: 07-settings-package
reviewed: 2026-10-29
depth: standard
review_scope: full_phase_01_through_05
diff_base: b185f0b
review_head: 5c8007e
phase_review_complete: true
native_strict_accepted: false
verification_limit: original_disk_preservation_failed
files_reviewed: 27
files_reviewed_list:
  - lookup/config.py
  - lookup/app.py
  - lookup/lifecycle.py
  - lookup/platform.py
  - lookup/gui.py
  - lookup/__main__.py
  - tests/test_config.py
  - tests/test_app.py
  - tests/test_lifecycle.py
  - tests/test_platform.py
  - tests/test_cli.py
  - lookup/settings_gui.py
  - tests/test_settings_gui.py
  - tests/test_app_gui.py
  - PKGBUILD
  - tools/stage_package.py
  - lookup/doctor.py
  - packaging/lookup
  - packaging/org.lookup.Linux.desktop
  - packaging/org.lookup.Linux.autostart.desktop
  - packaging/THIRD-PARTY.md
  - README.md
  - tests/test_doctor.py
  - tests/test_package.py
  - tools/check_package_vm.ps1
  - tools/check_settings_app.py
  - tests/test_check_settings_app.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: 1
status: clean
---

# Phase 7: Final Code Review

## Final assessment

Standard review of the complete source scope from `b185f0b` through `5c8007e` found **no open BLOCKER or WARNING**. The prior WR-01 fix remains resolved; its original evidence and disposition are retained below. All reviewed files meet the reviewed correctness/security standards; no additional concrete issues were established. This code-review result does not turn the native acceptance report into a pass.

The final production implementation is `a48fce1`; later commits add the acceptance harness/evidence and clarify README removal behavior. Final diff inspection found no subsequent production change requiring a repeated broad suite. Unit 05 review, threat-model checks and the unresolved preservation limit are recorded at the end. The incremental sections below retain their original review-time scope and pending statements as history.

## Completed Units 01–02

Independent standard review of committed changes from `b185f0b` through `c4e4f24` found no concrete BLOCKER or WARNING in this scope. Source was read from the committed snapshot so concurrent work on later units was excluded. This is not a whole-phase clean result: Settings/doctor/package implementation and real lifecycle acceptance remain pending review and execution.

Reviewed boundaries:

- Config validates edited fields before writing, merges specified changes without discarding existing clients/unknown fields/configured missing dictionary IDs, and uses a private sibling temporary file with flush/fsync/atomic replacement. I/O and validation failures preserve the previous destination.
- Reload retains the same Engine and monotonically invalidates lookup identities. Resources close/reopen on the worker; acknowledgements carry a separate revision. Background network holders do not retain the SQLite connection, and their completion cannot enrich stale history or mutate existing learning snapshots.
- Shortcut edits use the discovered four-field owned component/action identity, typed DBus arguments, availability checks, exact readback and explicit rollback failure. Ordinary entry registration does not call the active shortcut mutation API.
- Desktop/autostart operations preflight both exact user paths, refuse symlinks/unowned collisions, and distinguish source entries from package-owned system entries. Installed migration removes only recognized source shadows. Source Exec/Path quoting is retained.
- Disabled `--autostart` returns before GUI import/Qt construction. Installed cold starts use `/usr/bin/lookup`; source starts use the explicit Python/check-out command. All production kdotool subprocess calls pass through the centralized helper resolver in `platform.run`.

## Focused Validation

Executed without live KDE mutations:

`python -m unittest tests.test_config tests.test_app tests.test_lifecycle tests.test_platform`

**72 tests passed, no skips**, 1.531 seconds. Tests cover injected shortcut conflict/readback/rollback paths, preflight ownership checks, config preservation/atomic failure, and reload barriers/thread ownership/stale-result suppression.

## Scope Remaining at the Preliminary Review

- Final source/integration changes after the reviewed snapshots and unit 05 actual acceptance evidence.
- Actual installed package/capture authorization, automatic KDE registration removal, dependency availability and clean-session diagnostic execution remain mandatory unit 05 gates. The submitted static package/doctor implementation is reviewed below.
- Final integration changes and unit 05 actual settings/key/login/package acceptance evidence.

Mock and core success do not establish that a new physical shortcut, actual login autostart or package removal works in KDE. Those are separate mandatory execution gates. No source/state files or live session state were changed and no commit was created by this review.

## Original Unit 03 Incremental Review

Reviewed the committed Settings implementation and integration through `c46ed0c`, including `dc8db45`, `35bdeae` and `c3f4c8a`, with an explicit file scope. Interleaved package/doctor changes and later uncommitted D-11 work were excluded. No concrete BLOCKER or WARNING was established in this increment.

- Apply copies the GUI draft before background work and serializes preparation, worker acknowledgement and rollback. Config/registry/discovery work runs off the Qt GUI thread; state transitions and widget access return through a queued signal. Editable controls remain disabled while Close stays usable.
- Active key mutation occurs only for an explicitly edited shortcut. Loading can show a KDE override without writing it back to config or changing the binding during unrelated edits. The previous config and actual key transaction are retained for restoration.
- Apply success requires the exact reload revision. Wrong, obsolete or post-completion acknowledgements cannot announce success. Resource restoration requests their own revision; save, runtime, key rollback, config rollback and unconfirmed restoration have separate fixed statuses.
- Closing/reopening a pending Settings window reuses its controller and submitted snapshot; hiding it does not cancel its transaction. Shutdown stops timers, restores a prepared/awaiting transaction where needed and waits for the off-GUI job before quitting. The same Engine and monotonic lookup identities are retained.
- Config's new `retain_missing=False` rollback seam restores the exact prior dictionary ID set while preserving unrelated keys/clients. Normal edits retain configured-but-unavailable IDs. Check/reorder operations keep IDs and enabled state independent of display labels.
- Owner routes reload events separately from lookup events, invalidates accepted popup work around application, and changes the timeout for the next popup only. Existing learning connection ownership is unaffected.

Inspected the focused Settings regression cases for stale acknowledgements, external overrides, write/reload/rollback failure, exact dictionary restoration, close/reopen, timeout and shutdown. The orchestrator's existing 692-test result was not duplicated with another broad suite. Actual physical-key, login, native appearance and effective dictionary/network behavior remain execution gates; the new folder/rescan clarification still requires implementation and incremental review.

## Unit 04 Incremental Review

Reviewed committed package staging, PKGBUILD, installed wrapper/desktop entries, diagnostics, CLI routing, attribution and Russian README through `20f2fb5`, including helper/LF normalization fix `8838b96` and doctor implementation `d850595`. No concrete BLOCKER or WARNING was established in this increment. The later README paragraph describing D-11's pending folder flow is not evidence that that flow is already implemented or accepted.

- Staging limits archive content to selected application Python/data and four packaging inputs. It rejects symlink sources and a nonempty or symlink output directory; selected paths must be ordinary files resolving inside the source root. Archive paths, ordering, ownership, timestamps and gzip metadata are deterministic, and text is normalized to LF before hashing. The local source digest replaces exactly one template placeholder.
- Upstream helper and Mueller downloads use the pinned URLs/hashes from research, with no third-party `SKIP`. Installation uses a private helper and fixed absolute wrapper/import path, includes application data, avoids a competing global kdotool executable and copies only required Mueller files. The package preserves the upstream helper bytes by disabling stripping/debug processing.
- Attribution retains the actual helper license and WordNet notice; project and Mueller precise licensing uncertainty is explicitly retained for this local recipe. No precise license grant or redistribution clearance is fabricated.
- Installed launch/autostart entries use the agreed desktop ID, absolute commands, KDE autostart restriction and ScreenShot2 authorization metadata. The absence of a custom removal hook follows the researched service-refresh design; automatic active-key removal still requires its actual uninstall gate before phase acceptance.
- Doctor routes before history/dictionary lookup initialization, performs no network/clipboard/capture action, uses bounded version probes, and reads dictionary indices through non-cache-writing reader paths. Discovery/decompression share an isolated child deadline; stdout is checked before diagnostics are consumed. Fixed messages omit source text, dictionary names/paths and exception payloads. Temporary session-environment changes are restored in a `finally` block.
- The apparent distinction between KWin's principal bus name and `org.kde.KWin.ScreenShot2` is valid: upstream KWin also registers the latter service alias. This suspected defect was ruled out against [KWin's ScreenShot2 implementation](https://raw.githubusercontent.com/KDE/kwin/master/src/plugins/screenshot/screenshotdbusinterface2.cpp).

Reviewed the deterministic archive/line-ending, fixed-wrapper, parser read-only, diagnostic timeout/private-error and CLI exclusivity tests. The existing orchestrator's 693-test result was not repeated with another broad suite. Native package install/remove, actual authorization/helper linkage and health diagnostics remain execution evidence to be reviewed with unit 05.

## D-11 Dictionary Folder Follow-up

Reviewed committed follow-up `17b3b22` and regression commit `2ac86e4`. For normal XDG/LOOKUP_DICTS destinations, the path is derived without creation, shown as selectable plain text, and directory creation happens only after an explicit click in the off-GUI controller. Native opening uses a local-file QUrl, not shell interpolation. Failure retains the copyable path. Opening permits unchanged-field Apply; successful worker acknowledgement refreshes discovered rows while preserving configured IDs/order/enabled state and unsaved draft fields. A pending folder operation does not perform an unintended config save and shutdown suppresses a later native-open completion.

### WR-01: Empty dictionary-root override disables unrelated Settings controls

**Classification:** WARNING
**Disposition:** RESOLVED in `a48fce1`. Empty roots now return an explicit unavailable-folder state instead of raising; the visible folder button is disabled with actionable LOOKUP_DICTS help, while the rest of Settings receives its valid config/baseline and remains usable. No fallback directory is invented and the shared discovery semantics remain unchanged.
**File:** `lookup/settings_gui.py:28` and `lookup/settings_gui.py:109`

**Issue:** `_dictionary_folder()` assumes `dicts.dict_roots()` always contains an element. A separator-only explicit override, `LOOKUP_DICTS=os.pathsep`, produces an empty root list under the existing resolver. Discovery can represent this empty dictionary set, but the new helper raises `IndexError`. That exception turns the entire asynchronous Settings load into `runtime_failed`; the window never receives its config/baseline, so online, autostart and timeout editors remain disabled alongside the dictionary section. This conflicts with keeping unrelated settings usable when no dictionaries are configured.

**Reproduction executed:**

```python
import os
from unittest.mock import patch
from lookup import dicts, settings_gui
with patch.dict(os.environ, LOOKUP_DICTS=os.pathsep):
    assert dicts.dict_roots() == []
    settings_gui._dictionary_folder()  # IndexError
```

**Fix:** Handle the empty-root case explicitly. Either normalize this override consistently in the shared resolver (with compatibility tests for its callers), or return a clear unavailable-folder state while still loading the other controls. Do not display a fallback directory that the worker will never scan. Add a real-widget regression for separator-only overrides proving that unrelated fields remain usable and folder failure stays localized.

No broad test suite was duplicated; the existing 697-test host result was supplied by the orchestrator. The direct empty-root reproduction above establishes the uncovered failure independently of those passing tests.

**Focused re-review:** Inspected the precise helper/load/help changes and the new real-widget regression. Independently ran `python -m unittest tests.test_settings_gui.SettingsTests.test_separator_only_override_keeps_other_settings_usable_without_inventing_folder` — **1 test passed**, no skips. It checks empty resolver/discovery results, disabled folder action, enabled unrelated fields and an acknowledged successful Apply. The original finding/reproduction is retained as history; no open code-review finding remains in the preliminary scope. Whole-phase status stays partial until final unit 05 review.

## Final Unit 05 Review

Read both complete native harnesses and their acceptance tests, the final report, clone-preparation record, enabled/disabled login observations, doctor cases, retention baseline and removal observations. Inspected the native scaled/dark screenshot: the form scrolls while Apply and Close remain accessible, unavailable IDs remain visible, and displayed key/dictionary states match the structured evidence. No new concrete code defect was established.

- Host physical input is restricted to the fixed clone UUID. Each invocation checks the clone name, MAC, forwarding identity, original powered-off state and, before input, clone running state. Key input accepts hex scancodes only. Screenshot paths are passed as arguments; native commands cross SSH as base64 JSON. COM locking is released in `finally`. The submitted helper does not boot, revert, delete or send input to the original VM.
- Target probes require the dedicated UID/home before session operations. Isolated XDG paths are installed before Qt; the actual graphical runtime/bus is retained. Controlled fixture/failure/provider seams are explicit and are separate from physical installed capture and login evidence. Native stale work uses a bounded hold with release during shutdown. Native output/command files are confined to the synthetic account's state directory; no personal profile cleanup is performed.
- The strict validator requires native-installed mode, every required product/cleanup key, exact boolean true values, and no error. It also refuses additional false values. Missing, skipped, integer-as-boolean and mock reports cannot pass. Independently loading the committed report returns **False**, with **14/14** product gates and **5/6** cleanup predicates true. No acceptance rule was relaxed for the preservation failure.
- Removal observations before manual refresh already show zero owned actions/keys and no remaining package paths. The later physical-input observation retains all three baseline hashes and advances the unrelated key marker. Final observation has no bus owner after actual tray Exit. README correctly tells users to quit before removal and does not claim pacman terminates already loaded code.
- Enabled/disabled observations show genuine distinct SDDM Wayland sessions, a stable installed `--autostart` owner in the enabled case, and no owner throughout the disabled interval. The observer never launches the product. Doctor's four installed cases preserve the byte inventory; the healthy/offline and missing-tool/damaged-dictionary statuses match expectations.

Independent fresh verification in this final review: `python -m unittest tests.test_check_settings_app` — **3 tests passed**; direct report validation yielded `strict_accepted: False`, `product: 14 / 14`, `cleanup: 5 / 6`. Inspected committed full-suite tails: host **701 tests OK, 8 skips**, target **701 tests OK, no skips**. Those broad executions were supplied by the executor, not repeated or claimed as this reviewer's run. No native boot/mutation or broad suite was duplicated.

## Mandatory Threat-model Cross-check

| Threats | Review disposition |
|---|---|
| T-07-01..04: config, reload/history, private errors, responsiveness | Reviewed validation/atomic replacement, worker ownership, generation/revision boundaries, fixed errors and asynchronous completion. No open code finding. |
| T-07-05..08: registry, desktop ownership, helper execution, session deadlines | Reviewed exact owned identity, collision/readback/rollback, symlink/unowned-file refusal, fixed helper resolution and finite production calls. Actual key/install/login evidence supplements the earlier source review. No open code finding. |
| T-07-09..11: GUI completion, responsiveness, native content | Reviewed queued completion, snapshot/revision acknowledgement, closing/shutdown restoration, plain content and fixed statuses; native scaling/failure evidence inspected. WR-01 resolved. |
| T-07-12..15: supply chain, capture authorization, doctor, removal | Reviewed pinned provenance/private helper, real installed authorized capture evidence, isolated read-only diagnostic probes, package-owned removal and automatic active-key disappearance. License uncertainty remains explicit; no clearance is inferred. No open code finding. |
| T-07-16: VM/session ownership and baseline preservation | Fixed clone targeting and independent disk identities are evidenced, but original byte preservation **failed**. This mitigation cannot be reported fully verified. See limit below. No reviewed operation establishing a production/harness cause was found. |
| T-07-17..19: profile privacy, acceptance truth, user data | Synthetic dedicated profile, strict false result and separate controlled seams retained. Actual removal retains config/database/unrelated-entry hashes and unrelated physical key functionality. No open code finding. |

## Unresolved Verification Limit and Agent Exception Recommendation

`original_preserved` remains **false**. The original VDI grew from 9848390144 to 9958490624 bytes and its recorded SHA256 changed from `9f2b4a34fe8ae0f73db8df281f9414a68c9e9483e3d981b7a288f53c5b18fd1c` to the independently checked `fd3c5382d73a5ebdf849c5abe2e974c227398b1389b5738d5729714aa9c401b1`. Recorded VBox logs establish a separate original-VM GUI run around 2026-10-28 15:55–16:11 UTC; they do not establish its actor. Independent full disks and clone-only workflow controls support separation from the accepted product exercises, but do not prove the original unchanged or explain away the hash difference. Earlier transient GuestProperty bookkeeping is a separate recorded change.

Recommend a **nonblocking agent exception for continuing product workflow under the user's --auto instruction**, with this exact verification limit retained in phase/state reporting. All product gates have independent evidence and no unresolved code/security defect was established; attributing the separate original run or restoring original bytes is outside this code review and must not be inferred or attempted to manufacture a pass. Keep strict `accepted=false`, do not mark original preservation verified, and do not describe this as human acceptance. This recommendation permits workflow continuation; it does not certify every plan success criterion.

Only this review artifact was edited. No source/state changes, live VM operations or commits were performed by the reviewer.
