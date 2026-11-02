---
phase: 09-hotkey-capture
status: passed
verified: 2026-11-02T11:33:00Z
verified_revision: 4623670af803696119ea64497a79c045cdd4664a
verified_tree: 29c5ea8414350e06fb1b0066418c6e38475599a1
score: 3/3
verification_kind: agent
---

# Phase 9 verification: passed

Implementation: 4623670. Agent acceptance on the owned KDE Wayland clone, not human testing or Danila's acceptance. Baseline failures remain in their raw files and 09-BASELINE.md; they were fixed, not overridden.

## Requirement evidence

| Requirement | Result | Current evidence |
|---|---|---|
| CAPT-06: hotkey over A followed by movement to B returns A | Passed | Five move_after_hotkey rows in 09-native-samples.json return bank at the original coordinates while the actual cursor is at B. 09-native-burst.json adds ten rapid physical chords; independent mouse evdev evidence in 09-native-burst-input-order.json proves movement 80.031 ms after the final kernel key, with bank retained. |
| CAPT-07: a subsequent scene change cannot replace the original | Passed | Five scene_change rows return bank after the fixture changes to river on the kernel chord. 09-native-cold-combined.json passes scene replacement plus movement with the daemon initially absent. |
| PERF-02: comparable measured improvement and fixed budgets | Passed | Both resident groups pass every bound fixed in 09-BASELINE.md. Raw samples: 09-native-samples.json; statistics: 09-native-metrics.json. Additional process-absent cold starts are reported separately. |

## Implementation

The native KWin plugin observes the existing configured shortcut before desktop/Python dispatch. It retains one bounded offscreen frame with timestamp-consistent cursor coordinates, excluding LookUp windows by daemon PID. A bounded pointer history prevents later-dispatched input from replacing key-event coordinates. No competing shortcut is registered.

The existing Python entrypoint and daemon consume the frame once via a sealed anonymous memory FD. Snapshot retrieval precedes resource/lookup queueing; recognition does not resample the live screen or cursor. Raw pixels are released before translation and on resource errors. PRIMARY precedence and generation/history guards remain.

Consumed-frame markers suppress late duplicate activations before they create a new generation or fall back to a newer live scene. Direct --trigger retries in that five-second window are coalesced too; a new physical shortcut always replaces the marker. Expired and failed captures fail closed.

## Comparable timings

Milliseconds, nearest-rank p95. Frozen is the same passive Engine endpoint as the baseline: frame/PNG and coordinates are ready for recognition. It includes dispatch, queueing and encoding and is an upper bound on actual pixel acquisition.

| Group | n each | Baseline frozen median / p95 | Final frozen median / p95 | Baseline visible useful median / p95 | Final visible useful median / p95 |
|---|---:|---:|---:|---:|---:|
| cold_resident | 5 | 342.263 / 351.868 | 181.068 / 237.414 | 1053.793 / 1106.957 | 870.585 / 1088.651 |
| warm_distinct | 20 | 350.308 / 362.585 | 201.885 / 253.271 | 1018.511 / 1098.510 | 884.520 / 1002.269 |

Both groups meet the unchanged predeclared budgets: frozen median <=300/p95 <=330; visible useful median <=1100/p95 <=1200. The warm frozen outlier of 375.461 ms remains in the raw data; p95 is 253.271 ms.

New compositor instrumentation measures actual raw acquisition separately: cold_resident median/p95 3.075/4.145 ms, warm_distinct 3.317/3.820 ms. This different endpoint is not substituted for the comparable frozen-event budget above.

Five process-absent cold starts verify process birth after input. Their raw capture median/p95 is 2.998/3.599 ms; visible useful result is 1201.523/1234.493 ms, including daemon launch. The resident frozen budget is not misapplied to startup; no process-absent before/after speed claim is made because that baseline is unavailable. The combined cold/movement/scene case returns original bank in 1275.093 ms.

## Verification

- Host full suite after final native input-order code: python -m unittest discover -s tests — 828 tests, OK, 11 skipped, 46.664 s.
- Target installed Python core/GUI/capture/timing suite: 69 tests, OK, 3.986 s. Python files are unchanged since that run; native behavior is covered by the current real-input cohort.
- Final cohort: 40/40 installed-entrypoint requests: 5 resident cold, 20 warm, 5 full cold, 5 movement and 5 scene changes. Each retains kernel timestamps, key release, optical useful-result proof and matching passive source events.
- 09-native-scales.json: original bank after movement at 125%, 150%, 200%; 100% is in the main cohort. Scale restored to 100%.
- 09-native-repeat.json: a fresh result with the previous popup visible.
- 09-native-security.json: unrelated-peer rejection, authorized first consumption, duplicate rejection and expiry rejection. Review limits: 09-SECURITY.md.
- Real makepkg build/install passes upstream checksums. All 39 source members match source archive, installed files and current workspace. The native ELF in the package matches the loaded installed module. Hashes/boot identity: 09-native-installation.json.

Final calls use normal installed /usr/bin/lookup --trigger and --app. A temporary site hook only records Engine events and numeric metadata; it does not replace the controller, OCR or providers. The hook was removed after testing. Baseline passive event logging uses the same frozen endpoint.

## Harness corrections and historical evidence

VirtualBox queues keyboard and mouse independently. An exploratory burst delivered B before the final guest key and did not implement A-then-B: key timestamp 204497700000 ns, pointer timestamp 204494424000 ns, 3.276 ms earlier. The initial failure file and guest development logs remain; exploratory failed probes are not counted as acceptance successes.

The final stress/scale sender waits for genuine guest kernel release acknowledgement, then moves the console pointer. Independent mouse evdev recording proves the final burst order and 80.031 ms delta. The five ordinary movement samples use immediate console movement and retain native key-time coordinates. No expected word was changed to make a failed probe pass.

## Limits and cleanup

Target: Arch, KWin 6.8.1-2, Qt 6.12, EGL, owned VirtualBox clone, 1280x800 and stated scales. The native private ABI requires rebuilding after KWin updates. Source runs without this module keep the ordinary backend, which cannot promise physical-key-time capture; lookup --doctor reports bridge availability. No new claim for other compositors/GPUs, second monitors or human hardware testing.

09-native-cleanup.json records restored keyboard/mouse ACLs, unchanged retained user configuration hash, removal of the hook and session script, removed test guest property and clone poweroff. Original VM was not controlled or entered. Public fixture evidence and source remain in the owned clone.

Built package: dist/phase09-hotkey/lookup-linux-0.2.0-1-x86_64.pkg.tar.zst; downloaded SHA256 matches the target build.
