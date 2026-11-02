# Phase 11 — Pre-execution Review

Reviewed: 2026-11-02. Independent static review of the three plans, locked context, research, approved native UI contract, validation map, roadmap/requirements and relevant existing interfaces. This is plan acceptance, not implemented-product acceptance.

## Result: VERIFICATION PASSED

No blocking or outstanding coverage issues. Execution may proceed in waves 1, 2 and 3. The mandatory research gate is supported by recorded live feasibility evidence; Plan 03 correctly requires separate integrated-product evidence rather than reusing the research layer as acceptance.

## Requirement and context coverage

| Requirement / decision | Planned delivery |
|---|---|
| CAPT-08: one captured scene, repeated selection | 11-01 retains one immutable OCR source and resolves subsequent logical points without capture, cursor resampling or PRIMARY reads; 11-02 paints that image and selects again; 11-03 verifies actual product frame/session identity and useful words while source ticks advance. |
| TRIG-05: retained hover and input isolation | 11-02 paints an opaque retained base before tint and consumes layer input; 11-03 measures delivered input independently at the same source process and verifies captured hover text remains selectable. |
| TRIG-06: return control, including real fullscreen | 11-01 owns frame/cancellation lifetime; 11-02 centralizes complete session teardown; 11-03 verifies Esc, close, repeat invocation and errors over actual fullscreen Wesnoth, plus timeout, external focus and process exit. |
| PRIMARY and ordinary lookup compatibility | Initial fresh PRIMARY retains existing precedence and no scene; later scene clicks bypass PRIMARY and use the existing OCR/lookup/history/enrichment path. |
| Initial OCR result and selected-word outline | Initial pointed lookup remains automatic; existing OCR Selection.box propagates through compatible Query/Event fields and maps to the retained image's recorded geometry. |
| Focus, timeout and cancellation | Owned popup/layer focus remains one domain; external focus ends the session. Late generations cannot restore either surface or mutate the newer card pair. No-hit is nonfatal; operational failures release the layer before ordinary error presentation. |
| Existing popup/cards/settings | Existing Popup and immutable displayed-result/card paths remain authoritative; Phase 10 preferences and ordinary popup behavior retain regressions. |
| Scope and preservation | No process suspension, extra shortcut, multi-word gesture, persistent scene feature or OCR algorithm rewrite. Pre-existing OCR/OMX edits are preserved; target inventory records their actual bytes honestly. |
| Concurrent VM authorization | Product probe uses the guarded independent clone and SSH2227, never the original VM/SSH2223; temporary profiles/processes are scoped and root owns final poweroff. |

## Structure, dependencies and wiring

Fresh GSD plan-structure checks return `valid: true`, zero errors and zero structure warnings for every plan. Each has two tasks with concrete files, action, automated verification and measurable done criteria.

| Plan | Tasks | Declared files | Wave | Dependency |
|---|---:|---:|---:|---|
| 11-01 | 2 | 2 | 1 | None |
| 11-02 | 2 | 4 | 2 | 11-01 |
| 11-03 | 2 | 6 | 3 | 11-02 |

Dependencies exist and are acyclic; all shared interfaces are introduced before consumers. Source/Frozen/Scene, Query/Event selection boxes, Engine scene methods and Owner signals are specified consistently. Request identity remains separate from scene identity; later points retain the raw frame rather than consuming or transforming away pixels needed by the UI. Existing package source staging recursively includes Python modules, so the new native widget fits that path; Plan 03 requires staged inventory agreement.

Responsibility-map ownership is respected: existing compositor capture, native Qt scene presentation, existing Python OCR/lookup/cards and measured compositor input delivery. There is no new public/network surface or weaker capture-peer validation. Threats cover point/session validation, bounded transient pixels, stale history/enrichment, input ownership, inert text, clone isolation and misleading evidence.

## Nyquist compliance

`11-VALIDATION.md` exists and maps all six tasks, required new test files and native product evidence. Every task has an automated command; no watch mode or unlinked missing-test placeholder is present.

| Task | Wave | Automated check | Coverage |
|---|---:|---|---|
| 11-01-1 | 1 | `python -m unittest tests.test_app -q` | Same frame, PRIMARY, geometry, existing pipeline |
| 11-01-2 | 1 | `python -m unittest tests.test_app tests.test_hotkey_capture -q` | Lifetime, cancellation, history and retained snapshot |
| 11-02-1 | 2 | `python -m unittest tests.test_selection_gui -q` | New native layer tests created in the same task |
| 11-02-2 | 2 | `python -m unittest tests.test_selection_gui tests.test_app_gui tests.test_settings_gui -q` | Owner integration and preserved behavior |
| 11-03-1 | 3 | `python -m unittest tests.test_frozen_product -q` | New product-evidence validator tests created in the same task |
| 11-03-2 | 3 | Full discovery plus explicit actual-product native acceptance in action/phase verification | Host/target regressions and real operational proof |

Sampling is 2/2 in every wave. New test files precede source changes under the planned TDD tasks; no framework installation is required. Research's gate-disposition section explicitly states RESOLVED, while untested variants remain honest acceptance limits. No PATTERNS.md exists, so pattern-file compliance is not applicable. No root AGENTS.md or project-local skill directories exist; supplied session directives are represented by scoped work, preserved edits and verification requirements.

## Accepted nonblocking note

**WARNING — feedback latency:** The final full regression command previously took about 42 seconds, exceeding the 30-second fast-feedback guideline. The orchestrator explicitly accepted this on 2026-11-02: it is a required final phase regression gate, earlier task checks are focused, and the declared strategy targets at most 60 seconds. Keep full verification; do not weaken native acceptance or introduce a new framework merely to shorten this final command. This does not block execution.

```yaml
issues:
  - plan: "11-03"
    task: 2
    dimension: nyquist_compliance
    severity: WARNING
    description: "Final full regression previously takes about 42 seconds."
    disposition: "Accepted by orchestrator; focused checks provide early feedback and final full regression remains mandatory."
outstanding_blockers: 0
outstanding_warnings: 0
```

No application was run and no product source was changed during this review. Implementation and final product acceptance remain pending.
