# Phase 4 VM results

Agent-operated acceptance on the existing VirtualBox arch-kde VM, Arch Linux,
Plasma 6 Wayland/KWin 6.8, Qt 6.12, installed PyQt6 and tesseract 5.5.3.
Isolated target checkout: ~/LookUpLinux-gsd-spike-04. No production daemon,
dictionary data, translation network calls or database writes are involved.

Reproduce from the Windows repository after syncing lookup/tests/tools:

```powershell
python tools/check_vm_spike.py --output .planning/phases/04-vm/04-GATE-RESULTS.json
```

The host invokes bounded --target actions over archvm SSH. Physical keys use
VBoxManage controlvm arch-kde keyboardputscancode, including explicit releases;
pointer input uses VirtualBox COM PutMouseEventAbsolute with a bounded relative
PutMouseEvent/feedback fallback when needed. This CLI cannot inject
mouse events, so COM is required. The fixed tray coordinates are calibrated to
this VM's 1920x1080 panel and checked through actual Qt menu/action events.
They are tooling for this spike, not a production interface assumption.

## Observed criteria

| Criterion | Evidence |
|---|---|
| SC1 / TRIG-01 | A unique desktop entry registers Meta+Shift+D via kbuildsycoca6 without relogin. Four physical keys wake one existing PID; after Quit a physical cold key starts a distinct single owner. Another owned component sees the binding unavailable; setup refuses an existing unrelated binding. |
| SC2 / CAPT-01 | Real cursor over independently positioned English glyphs produces english at scale 1/1.25/1.5/2 from 1920x1080 monitor captures. Actual pixel/logical ratios are used. Only one Virtual-1 output is exposed; optional second monitor unavailable. Negative origins remain portable tests. |
| SC3 | KWin geometry equals the intended clamped popup target; active UUID and Qt active state agree. Physical Escape hides the popup. Separately activating the public fixture produces deactivate. The visible panel tray icon opens its native menu via physical right-click, and a physical menu click emits tray-action. |
| SC4 | Existing primary offer is read in a few milliseconds; only presence and elapsed time are recorded. No clipboard contents/history are modified. Probe/capture/OCR/total timings are recorded for every scale. |

The structured JSON retains the precise samples, owner PIDs, input points,
compositor targets, active UUIDs, event reasons, primary timing and restoration
flags. Final completed run: capture medians 370.1ms Spectacle and 82.1ms ScreenShot2;
all ten backend samples recognized the public word. Four-scale total median
396.7ms (probe + capture + OCR), with 383.6–425.6ms across scales. This
measures the Phase4 spike, not the later translation/card end-to-end budget.

## Decisions and fixes discovered experimentally

- Choose kdotool cursor/window operations. No KWin fallback script was needed,
  loaded or installed. Owned UUID/PID checks precede move/raise/activate.
- Choose ScreenShot2 for production capture; both candidates work, but its
  lower measured cost leaves more of the 1.5s budget for dictionary/translation.
- Initialize the QtDBus session connection before PyQt argument conversion.
  ScreenShot2 returns raw RGBX8888 with stride metadata, not a PNG. Concurrent
  draining starts before the blocking call; exact bytes and format are checked,
  the QImage is detached, and PNG transport remains in memory.
- Set the KDE Qt platform theme in the owner for Breeze icons/native tray menu.
  Use QCoreApplication in launcher/status clients to avoid GUI activation effects.
- KWin geometry is authoritative for Wayland position; Qt may report (0,0).
  Initial focus settling precedes arming deactivate handling; cold-start checks
  wait for this state before deliberately testing focus loss.
- VirtualBox can suppress repeated identical absolute pointer events after
  guest display changes. A one-pixel adjacent event followed by the intended
  event, then KWin cursor confirmation, provides reliable delivery evidence.
  A bounded relative-input correction path handles absolute-device stalls;
  the final recorded run used the absolute route at all four scales.

## Cleanup and limits

The host's finally block independently releases keys, attempts target rollback,
and writes evidence. Target snapshots predate mutations, carry a fresh run UUID,
record process identities, and retain failed restoration state for recovery.
The final live run passes display_restored, desktop_restored, processes_stopped
and shortcut_restored. Only spike-owned entries/processes are removed; unrelated
desktop applications/settings remain outside the experiment.

No frames, activation tokens or primary-selection contents are committed.
Transient inspection images were removed. No KWin focus/capture/lock policy or
global interpreter allowlist changed. Normal VM session unlock was sufficient.
The VM automatically locked again during prolonged validation; setup now
rechecks ScreenSaver.GetActive, discovers only the current user's Wayland
session via loginctl, requests normal unlock, and confirms the unlocked state.
Runs made while locked failed honestly and restored their owned resources;
their missed hotkeys are not classified as accepted application behavior.
The independent security check closed T-04-01..14; review fixes cover inherited
stdout, partial setup, lost response, key-release failure and false restore passes.

528 tests pass on each Windows interpreter (3.14 and 3.12, 7 existing skips each)
and Arch 3.14 (3 skips). Arch's historical canceled multiprocessing workers emit
SemLock teardown traces while the suite itself succeeds. Real MDX/DSL consumer
files and friend hardware remain outside this phase; no human test is claimed.
