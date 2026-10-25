# Phase 4: VM platform spike — Research
Researched 2026-10-25. HIGH confidence for probed APIs; runtime SCs still pending.

## User Constraints (from CONTEXT.md)
### Locked Decisions
- D-01: Use existing VirtualBox arch-kde through ssh archvm. The roadmap's
  QEMU/virtio wording is superseded by the recorded Windows/VirtualBox choice.
  Do not recreate or replace the VM. It is now running headlessly with an
  active Plasma Wayland session for arch (UID1000), wayland-1, KWin PID471
  at the latest probe. Discover current session values; do not hardcode PIDs.
- D-02: Reuse Phase 3's accepted OCR library and explicit physical-image point
  contract. Geometry transforms for scale1/1.25/1.5/2 and negative monitor
  origins must have portable behavioral tests, independently of VM rendering.
- D-03: Evaluate installed kdotool first for cursor, window positioning and
  activation. If cursor or move/focus is unsupported/unreliable, implement the
  roadmap's narrow KWin-script + QtDBus receiver fallback. Persist an observed
  decision in PROJECT.md before Phase 5; do not assume commands exist.
- D-04: Measure spectacle monitor capture first, including correct monitor,
  cursor inclusion and privacy/cleanup. If capture threatens the latency
  budget, probe ScreenShot2 DBus. Prefer an FD/in-memory path if available.
  Never retain private desktop PNGs as test artifacts. Capture a controlled
  public test window when demonstrating OCR; unrelated desktop text stays out
  of logs/repository. Record per-stage probe/capture/OCR timings.
- D-05: A uniquely named test .desktop entry with X-KDE-Shortcuts and
  kbuildsycoca6 should wake one already-running test process via Qt single-
  instance IPC. Repeated triggers must prove the same PID. Test Meta+Shift+D
  registration, relogin necessity and conflicts; preserve unrelated shortcuts
  and configs, back up/restore only any spike-owned entry touched.
- D-06: Use a minimal frameless Qt popup and QSystemTrayIcon/Menu in the active
  Plasma session. Prove actual pointer-adjacent monitor-clamped placement and
  focus; distinguish Escape from focus loss. Research activation token paths
  rather than disabling KWin focus protections. Record what is observed versus
  inferred. Avoid broad system-policy changes or new daemon architecture.
- D-07: Probe wl-paste --primary with ~0.5s timeout; no hanging subprocesses.
  Avoid modifying unrelated clipboard/history; selection tests use known public
  text and leave no copied screenshot/text artifacts behind.
- D-08: Test target scales100/125/150/200 and second monitor if exposed by VM.
  Restore display configuration after experimental changes. Record unavailable
  hardware explicitly; do not invent multi-monitor measurements. Autonomously
  accept observed evidence and carry honest external limits forward.
### Deferred Ideas
Production popup/data/settings belongs to5, words/review to6, packaging to7,
hardening to8. No global security/focus changes or VM recreation.
[VERIFIED: 04-CONTEXT.md; full canonical deferred text remains there]

## Summary and Ownership
Use pure geometry plus small bounded platform adapters and one Qt spike host.
Reuse accepted lookup.ocr and CLI privacy/timing conventions. Candidate owners:
pure monitor/pixel/clamp functions; kdotool window/cursor adapter; capture
adapter; unique QtDBus spike service/popup/tray; VM harness. No production app.
[VERIFIED: lookup/ocr.py, lookup/__main__.py, Phase3 verification, context]

## Fresh Environment Evidence
- kwin6.8.1-2, kglobalacceld6.8.1-1, qt6-wayland6.12.0-1,
  python-pyqt6 6.11.0-4; session bus and UnixFD passing available.
- kdotool0.3.0 getmouselocation succeeded: x960,y540,screen0,window UUID.
- Virtual-1 is the only connected/enabled output:1920x1080,origin0,0,scale1.
- StatusNotifierWatcher host registered=true.
- IMPORTANT: ScreenSaver.GetActive=true; primary --list-types=x-kde-lockscreen.
  Session is locked. Do not treat locked-screen failures as application bugs.
[VERIFIED: read-only SSH probes; no configs/clipboard/capture changed]

SSH lacks Plasma environment: initial kdotool --help falsely reported
unsupported KDE. KDE_SESSION_VERSION=6 fixed it. Current probe values:
XDG_RUNTIME_DIR=/run/user/1000; DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus;
WAYLAND_DISPLAY=wayland-1; QT_QPA_PLATFORM=wayland; XDG_SESSION_TYPE=wayland.
Discover current values, do not hardcode PIDs. [VERIFIED: paired probes]

## Concrete APIs and Pitfalls
### Cursor/window and fallback
Live kdotool help supports getmouselocation, search --pid/--title,
getwindowgeometry, getactivewindow, windowmove, windowactivate, windowraise,
kwinscript --file/--inline. Parse output; never eval --shell. Match spike
PID+unique title→UUID; re-query compositor geometry/active UUID after actions.
No keyboard/mouse injection commands: invokeShortcut is not proof of a keypress.
[VERIFIED: target help; CITED: https://github.com/jinliu/kdotool]

Live /Scripting: loadScript(filePath[,pluginName])->int, start(),
unloadScript(pluginName)->bool. Fallback uses workspace.cursorPos/screens,
Window.frameGeometry, workspace.activeWindow and async callDBus to a narrow
QtDBus receiver. Unique name; unload finally; target only owned UUID/PID.
[CITED: https://develop.kde.org/docs/plasma/kwin/api/; VERIFIED: introspection]

Geometry: subtract monitor logical origin before multiplying actual captured
pixel/logical-size ratios. Preserve negative origins and fractional scale;
clamp popup logical rect to selected monitor available area. Pure tests cover
1/1.25/1.5/2 and edges; use actual dimensions rather than nominal scale alone.
[VERIFIED: arithmetic and D-02]

### Spectacle first; FD capture if needed
Live flags: -b background,-n nonotify,-m current,-o explicit filename.
-p includes cursor;-c/-C copy image/path. Omit -p/-c/-C; use finite timeout
and finally cleanup. Only controlled public text; no retained desktop PNGs.
A memfd /proc/self/fd path is an EXPERIMENT: delegated existing Spectacle
process may not own that FD. Do not assume this path works.
[VERIFIED: target --help; proposed execution experiment]

Live ScreenShot2 v5 service org.kde.KWin, path /org/kde/KWin/ScreenShot2,
interface org.kde.KWin.ScreenShot2:
CaptureScreen(QString,QVariantMap,QDBusUnixFileDescriptor)->QVariantMap;
CaptureArea(int,int,uint,uint,map,FD)->map; ActiveScreen(map,FD);
CaptureWindow(QString,map,FD). FD transport was confirmed.
[VERIFIED: live introspection; full names CaptureActiveScreen/CaptureActiveWindow]

Reply is RAW QImage storage, not PNG: type,format,width,height,stride,scale.
Options: include-cursor,native-resolution,hide-caller-windows(default true).
Validate exact stride*height, format and caps; finite pipe drain; detach QImage
before bytes die; close all originals/duplicates. If caller owns public text
window, test hide-caller-windows=false or use a separate content process.
[CITED: https://raw.githubusercontent.com/KDE/kwin/Plasma/6.8/src/plugins/screenshot/screenshotdbusinterface2.cpp]

Policy changed:6.7 source checks restricted interfaces;6.8 removes that check.
Safe nonexistent-output probe from unprivileged Python returned
org.kde.KWin.ScreenShot2.Error.InvalidScreen, not NoAuthorized. No pixels taken.
Do NOT whitelist /usr/bin/python3 or change global policy. Spectacle's desktop
still declares restricted interface, which does not prove current enforcement.
[VERIFIED: target safe probe/desktop fields; CITED: KDE screenshot source6.7/6.8]

Successful PyQt invocation shape (safe probe only):
```python
msg = QDBusMessage.createMethodCall("org.kde.KWin",
    "/org/kde/KWin/ScreenShot2", "org.kde.KWin.ScreenShot2", "CaptureScreen")
msg.setArguments(["__lookup_invalid_output__",
    {"include-cursor": False}, QDBusUnixFileDescriptor(write_fd)])
reply = bus.call(msg, QDBus.CallMode.Block, 2000)
```
EMPTY {} yielded PyQt_PyObject marshalling error; empty QDBusArgument map
disappeared from signature. Nonempty dict+direct FD wrapper works. Wrapper
duplicates original FD; caller closes original, not wrapper-owned duplicate.
[VERIFIED: probes; CITED: https://doc.qt.io/qt-6/qdbusunixfiledescriptor.html]

### Shortcut, single instance, activation, tray
Use unique .desktop with Type=Application,absolute Exec,Terminal=false,
StartupNotify=true,X-KDE-Shortcuts=Meta+Shift+D. Keep Qt desktopFileName aligned.
KGlobalAccel upstream maps X-KDE-Shortcuts to _launch, launches KIO job and
watches KSycoca changes. kbuildsycoca6 hot-refresh/relogin behavior still needs
observation. Query availability first; conflict test only spike-owned entries.
[CITED: KDE/kglobalacceld src/kserviceactioncomponent.cpp and globalshortcutsregistry.cpp;
VERIFIED: target isGlobalShortcutAvailable/getComponent/invokeShortcut interfaces]

Recommend session-bus name ownership as atomic single-instance gate; bounded
Trigger method forwards primitives/token and returns owner PID. Cold command
becomes owner; repeats contact existing host. QLocalServer is acceptable but
avoid PID-file races and broad daemon design. [VERIFIED: D-05; recommendation]

XDG activation token travels via XDG_ACTIVATION_TOKEN or Application platform
data activation-token; forward to existing process, unset in child before
subprocesses, never log token. Token consumption through public PyQt setter
was NOT verified. Test requestActivate then kdotool activate; fall back narrowly
if needed. Show/requestActivate success is not focus proof; check active UUID
and Qt isActive/events. Do not disable focus prevention.
[CITED: xdg-activation-v1 protocol; https://doc.qt.io/qt-6/qwindow.html]

QSystemTrayIcon+QMenu with retained objects,real icon,quitOnLastWindowClosed=false.
Watcher capability is not icon visibility/menu proof. Record separate Escape
and focus-loss reasons from actual events. [VERIFIED: D-06 and target watcher]

### Primary and scale restoration
wl-paste --primary --no-newline,timeout~0.5s,bounded bytes,fixed errors. Research
only listed types; did not read/modify clipboard contents. kscreen-doctor -j
gives name/id/pos/scale/currentModeId and mode dimensions; help supports
output.NAME.scale.VALUE and fractional Wayland scale. Save affected settings,
run four scales, restore finally and compare JSON. One output currently;
record missing second monitor honestly while pure tests cover negative origins.
[VERIFIED: target flags/help/JSON; D-07/D-08]

## Validation and Security
See04-VALIDATION.md: pure geometry/parser/cleanup/failure tests plus four real
SC gates. Never count mocks, skipped tests or D-Bus invokeShortcut as actual
keypress/capture/focus evidence. Existing full suite remains regression gate.
[VERIFIED: phase requirements and repository conventions]

Threat register: JS/command injection,IPC identity/message bounds,duplicate-owner
race,FD/child hangs,raw-image caps,private frames/tokens in logs,clipboard writes,
shortcut/display collateral changes. Use fixed argument/service/path names,
finite deadlines,per-user ownership,narrow owned-key restore and finally cleanup.
[VERIFIED: boundaries from D-03..D-08; proposed mitigation plan]

## Execution Checks — No Interview Gate
Host follow-up after research: normal `loginctl unlock-session 1` succeeded;
ScreenSaver.GetActive returned false. Lock policy was not changed. Reprobe the
current session before each live run; the locked observation above is history.

Normal authorized session unlock; kdotool move/focus versus fallback gate;
Spectacle versus FD timing gate; desktop cache/relogin/conflict/actual key;
four-scale public capture→OCR; popup/tray/event proof; primary timeout; restore
settings and remove frames/scripts/FDs. Persist observed decisions in PROJECT.md
before5. These are execution tasks, not unanswered planning questions.
[VERIFIED: explicit --auto instruction and roadmap]

## Sources/Confidence
Primary: live VM introspection/help/probes; official KDE kdotool/KWin/
kglobalacceld source; Qt QWindow/UnixFD docs. Policy6.7→6.8 difference verified
against official KDE raw source and target invalid-screen dispatch.
Confidence HIGH for APIs; capture latency/focus/shortcut outcomes are unmeasured.
No screenshots,registrations,focus changes,display changes,clipboard writes or
package installations occurred during research.
