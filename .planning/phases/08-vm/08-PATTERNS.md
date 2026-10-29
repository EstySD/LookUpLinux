# Phase 8 — Pattern Map

Mapped 2026-10-29 from 08-CONTEXT/RESEARCH/VALIDATION. New tool names below are suggestions, not implementation decisions. Five analog families suffice; no production changes made.

## File Classification

| Likely file | Role / flow | Closest actual analog |
|---|---|---|
| lookup/app.py, lookup/gui.py timing hooks | service/controller; event-driven | Existing Event.elapsed_ms, Result.timings, Engine identity guard, Owner.receive/present |
| tools/check_performance.py and tests | test/utility; batch/event-driven | check_context_app.live, check_settings_app status/login_probe; test_check_settings_app |
| tools/check_stability.py and tests | test; batch/process/file-I/O | check_settings_app.environment/status and strict accepted; test_app identity/history contracts |
| tools/check_games.py or game scenario helpers | test; event-driven | Guarded check_package_vm.ps1 input/screenshot; no existing real-game oracle |
| clean install/login/remove driver | test; batch/file-I/O | check_package_vm.ps1, check_settings_app.login_probe/removed_probe, stage_package.py |
| geometry/fault regressions if actual defects found | test; transform/request-response | tests/test_platform.py, test_app.py; capture_monitor/image_point/popup_rect |
| Phase8 JSON/raw samples/screenshots | evidence; append/snapshot | Earlier required-gate reports; retain failed attempts and carry-forward exception |

## Pattern Assignments

### Numeric timing hooks: app/gui boundary

Source lookup/app.py:292–296, 334–344:

```python
timings=dict(result.timings,**query.timings)
for key in ('first_useful','meaning_ready'):
    if timings.get(key,0)>0:
        timings[key]+=lookup_offset
```

Engine emits ready/context with elapsed_ms from perf_counter and current(identity) guards. Keep these monotonic stage values and accepted IDs; do not log query/context/translation/token. Source lookup/gui.py:545–557:

```python
identity=self.engine.begin()
self._identity=identity
self._clear_displayed()
self.popup.hide_for_capture()
QTimer.singleShot(75,lambda:self.engine.enqueue(identity) if self.engine.current(identity) else None)
```

Owner.receive (561–584) distinguishes frozen/loading, ready/useful and context/enrichment. present (585–607) positions and calls popup.show(), then schedules focus. Hook numeric daemon LOOKUP_TIMING at those boundaries, preserving CLI behavior and queued-thread ownership. Neither ready nor show/isVisible proves compositor-visible useful content. Existing elapsed_ms starts after dispatch; new external input/visible-frame bracket must include that omitted work.

### Guest observation and strict report acceptance

Source tools/check_settings_app.py:21–25:

```python
if not isinstance(report,dict) or report.get('mode')!='native-installed' or report.get('error'):return False
return all(isinstance(report.get(group),dict) and keys.issubset(report[group]) and
           all(value is True for value in report[group].values())
           for group,keys in (('gates',REQUIRED_GATES),('cleanup',REQUIRED_CLEANUP)))
```

Reuse strict booleans/required keys and fixed error reasons, but define Phase8 gates independently. Do not copy Phase7 original_preserved=true requirement or modify its raw false report; carry its historical exception explicitly. tests/test_check_settings_app.py rejects missing/false/None/1/skipped gates, mock modes, cleanup failure and false extra observations. Add meaningful malformed clock/sample, null live success, missing game route and stress-oracle rejection cases.

Guest environment analog check_settings_app.py:28–39 asserts owned UID/home, imports installed /usr/lib/lookup/app, resolves session env, sets all three XDG roots and strips inherited SUDO_* ownership hints. Isolate before Qt. Status/login_probe (137–159) is read-only: it samples /proc cmdline and start_ticks plus loginctl session metadata and explicitly never launches product while observing login. Reuse PID/start identity for cold-run correlation, extend /proc with RSS/threads/FD/recursive-child samples. Preserve raw data and predeclared thresholds; a process alive flag alone is insufficient.

### Owned host input and framebuffer

Source tools/check_package_vm.ps1:11–20 pins clone UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8, name lookup-gsd-07, MAC080027A05376, port2227; checks original powered off and requires clone running for mutations. Actions Keys/Pointer/Relative/Scroll/Screenshot are already available:

```powershell
& $lookupVBox controlvm $lookupVm keyboardputscancode @($Codes.Trim() -split '\s+')
& $lookupVBox controlvm $lookupVm screenshotpng ([IO.Path]::GetFullPath($Output))
```

COM mouse access locks the exact machine and unlocks in finally. Reuse guard/explicit UUID and key release semantics. Extend attachment/path validation if needed; never call old check_app.py host helpers directly: line551 still hardcodes arch-kde. Likewise old 04 spike automation is a pipeline analog only, not a safe VM controller.

Host Native currently targets lookup07/check_settings_app.py; a new owned account/driver must explicitly validate its identity and path rather than silently reuse old account assumptions. Record real input sequence with full releases. Screenshot returns a real framebuffer; add request-specific useful-content detection and bounded visibility brackets, not fixed sleep-as-latency.

### Real capture, geometry and live meanings

lookup/capture.py:147–169 uses perf_counter, returns Capture(png,w,h,backend,elapsed_ms); screenshot2 stays in-memory. Spectacle alone creates TemporaryDirectory(prefix='lookup-capture-') and a scoped frame.png. app.Source uses screenshot2. Privacy/fault oracles must observe this production path; killing unrelated Spectacle is insufficient.

lookup/platform.py:122–139:

```python
return ((point[0]-monitor.x)*w/monitor.width, (point[1]-monitor.y)*h/monitor.height)
```

Reuse image_point actual pixel/logical ratios and popup_rect bounded work-area placement; tests/test_platform.py already includes geometry/negative-origin cases. Do not assume scale equals screenshot ratio or game locked pointer equals center.

tools/check_context_app.py:46–92 supplies a finite live corpus through production translate.lookup(context_span=...,context_complete=True), records first_useful/meaning_ready and matching persistence, then restores env in finally. Copy corpus/exact-span orchestration only: its passed calculation expects all replies/cache success and must not become Phase8 availability statistics. Report attempted/succeeded/reasons and null successful-latency metrics for zero public successes; controlled held replies remain separate.

## Shared Patterns and Missing Analogs

- unittest, injectable delayed providers/events and fixed private errors; production Engine and SQLite ownership unchanged unless a demonstrated defect requires a small fix.
- Required gates, bounded subprocesses, finally cleanup, owned paths/account/service, synthetic evidence only; preserve layout/network/input and end clone powered off.
- No existing passive evdev/kernel-clock observer, cross-boundary dispatch clock or compositor-visible matcher. Implement the researched single-clock/upper-bound contract, record uncertainty and never subtract unrelated clocks.
- No existing real-game renderer/fullscreen/locked-cursor/fresh-frame/resumed-input oracle. Actual game data/process and observed gameplay changes are mandatory; Qt fixtures or menu screenshots alone cannot fill them.
- No current sustained RSS slope/privacy Klipper oracle. Explicit baseline/denominators/count integrity/restoration are new test responsibilities, not proof supplied by old scripts.
