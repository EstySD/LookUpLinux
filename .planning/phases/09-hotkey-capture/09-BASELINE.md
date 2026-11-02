# Phase 9 baseline — 2026-11-02

Runtime behavior has not been optimized when these budgets were fixed.

## Environment and method

Owned clone lookup-gsd-07, UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8, independent disk 2712d710-daaa-449c-843d-d570091127bc, pinned SSH2227 and guest DMI 097920cf-b594-494b-8bd8-ccff973c1dc8 verified. lookup07 has an active KDE Wayland session at 1280x800/100%. Original VM is externally running; it was neither controlled nor accessed as a guest. The old input helper's original-OFF precondition was not applicable; a private clone-only input helper checks the owned identity instead.

Installed package 0.1.0 differs from current source. Baseline therefore runs an isolated current source snapshot in `/home/lookup07/Projects/gsd-phase09-20261102` with separate `lookup-phase09-baseline` data, offline Mueller dictionary and unchanged existing shortcut. Existing user OCR changes are included. Passive Engine event logging records frozen time; existing timing instrumentation records Trigger/useful presentation. The existing optical/evdev observer supplies real kernel hotkey timestamps, verified popup pixels and released-key evidence. Neither simulated providers nor injected OCR supplied these results.

The private launcher constructs the normal Owner without changing installed desktop entries. It preimports typing to avoid a Python 3.14 concurrent typing/dataclass import failure observed in the first harness startup. That failure is retained as a harness startup limitation, not counted as a successful request.

`cold_resident` means the first request after explicitly restarting the daemon, with resources opened normally. It does **not** include daemon process launch after the hotkey, reboot, or dropped filesystem caches. `warm_distinct` uses 18 synthetic dictionary scenes plus two repeats, in a resident daemon. Full process-absent cold hotkey acceptance remains outstanding. The five cold and twenty warm samples are retained in `09-baseline-samples.json`; exploratory setup attempts 1–5 are not part of that fixed workload.

Capture endpoint is the frozen Engine event after frame/coordinates and PRIMARY/work-area handling, a conservative upper bound on frame availability. Result endpoint is the end of the first optically verified useful popup frame. It includes actual Python trigger dispatch and observer sampling overhead, recorded separately from internal telemetry.

## Results

Nearest-rank p95; all 25 measured requests succeeded.

| Group | n | Hotkey→frozen median / p95 | Hotkey→visible useful median / p95 |
|---|---:|---:|---:|
| cold_resident | 5 | 342.263 / 351.868 ms | 1053.793 / 1106.957 ms |
| warm_distinct | 20 | 350.308 / 362.585 ms | 1018.511 / 1098.510 ms |

## Budgets fixed before optimization

For the same resident-daemon workload and observer, both groups must have capture median ≤300 ms and p95 ≤330 ms; visible useful median ≤1100 ms and p95 ≤1200 ms. These require a measurable capture improvement without materially regressing first results. They are agent-selected experiment budgets, not a claim of human approval or instant capture. Full cold-start and temporal correctness remain separate mandatory acceptance gates.

## Temporal correctness probes

- Real hotkey over A=(684,376), immediate hardware pointer movement to B=(100,100): frozen event used **B**, then `not_found`. CAPT-06 fails. Raw evidence: `09-movement-baseline.json`.
- Real hotkey over `bank`, fixture changes its text on receipt of the kernel chord: unchanged pointer, ready result **river**. CAPT-07 fails. Raw evidence: `09-scene-baseline.json`.

These are baseline failures to fix, not accepted exceptions. Snapshot immutability after Source.freeze does not satisfy either requirement.

## Reproducibility

Private harness derives from `tools/check_hardening.py`: isolated root/source/launcher paths; clone-only hardware input; an extra passive frozen-event timestamp; scene-change probe alters only the public QLabel. Copies are retained beside the staged target source. No original VM policy, system compositor policy, installed package or retained user config was changed. Keyboard input ACL was saved before granting synthetic lookup07 read access and must be restored during cleanup.
