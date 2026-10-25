---
phase: 02-offline-dicts-translate
verified: 2026-10-25T12:15:00Z
status: human_needed
score: 5/5 success criteria verified by automated and VM checks
behavior_unverified: 0
human_verification:
  - test: Confirm the CLI user flow and readable dictionary/online output meet the Phase 2 goal.
    expected: Dictionary articles, ran-to-run lookup, cache hits, phrase saves and sentence translation behave as recorded in 02-VM-RESULTS.md.
    why_human: The verify-work workflow requires a confirmation summary even when all deliverables have passing automated coverage; user acceptance has not been supplied.
---

# Phase 2: Offline Dictionaries and Translation — Verification

Implementation and machine-verifiable requirements are satisfied. Phase
acceptance remains pending the verify-work confirmation checkpoint.

## Success Criteria

| Criterion | Evidence | Outcome |
|---|---|---|
| SC1: Folder-driven multi-format dictionaries, ordered articles and metadata | StarDict/DSL/MDX fixture suites; discovery/config/CLI tests; VM Mueller: 46231 entries, 1 skipped, run IPA rʌn and n/v senses | verified |
| SC2: Exact and base-form lookup | Lemma suite, both real Mueller sample tests on Windows and VM, twelve CLI probes | verified |
| SC3: Cache bypasses network | Translation/CLI forbidden-network tests; VM repeat run has online=0.000ms | verified |
| SC4: Online fallback works in the VM | All Google clients and MyMemory answered through application urllib; evidence-backed decision retains MyMemory | verified |
| SC5: Context, phrase and failure behavior | Parallel context tests, VM sentence/phrase SQL checks, refused/blackhole probes preserve article and return within about 3.2s | verified |

## Requirement Traceability

| Requirement | Implementation | Evidence |
|---|---|---|
| TRAN-01 | dictzip.py, stardict.py, dsl.py, mdx.py, dicts.py, __main__.py | Reader/discovery/CLI tests; real Mueller VM checks |
| TRAN-02 | online.py, translate.py | Provider/parser/deadline tests; four live provider probes and proxy failures |
| TRAN-03 | store.py schema v2, translate.py cache | Cache tests, CLI repeat, VM network time zero |
| TRAN-04 | dicts.py, data/irregular.txt | Candidate and pointer tests, real sample forms |
| TRAN-05 | translate.py context worker | Bounded-thread/cache tests, successful and failed context rendering |
| DATA-03 | translate.py classification and persistence | Tests and VM SQL show only run and break out, no sentence/non-word rows |

## Artifact and Integration Checks

- Eleven plans have eleven matching summaries. Every planned source module
  and test module exists; the CLI calls actual DictSet and translation APIs.
- Readers use shared immutable Article/SearchResult; lazy imports avoid cycles.
- DictSet concatenates all ordered dictionaries, validates base candidates
  against dictionary contents and resolves pointers without recursive loops.
- Config IDs are compared against discovery results, never joined to paths.
  Walk depth/candidate limits, hidden/symlink exclusions and failure isolation
  are covered by tests, including POSIX symlink checks in the VM.
- Cache payloads are validated; SQL uses bound values; context workers never
  use the SQLite connection. Existing Phase 1 tests also passed.
- Core imports remain stdlib-only, Qt-free and create no filesystem artifacts.
  AST and behavioral privacy checks find no library printing/logging or query
  leakage in transport failures. CLI stderr uses fixed messages/type names.
- No dictionary archive, real dictionary file, cache or database was committed.

## Verification Results

- Windows 3.14: 482 tests, OK, 6 skips, 20.583s.
- Windows 3.12: 482 tests, OK, 6 skips, 20.045s.
- Arch Python 3.14.8: 482 tests, OK, 2 skips, 10.801s.
- Real Mueller VM suite: 2 tests, OK, no skips, 0.152s.
- Focused final check: 27 tests, OK, one Windows POSIX skip, 3.189s.
- D-09 VM opening: median/max 91.0515/110.784ms; search 4.8395/7.708ms.
- Full live commands and observed results are in 02-VM-RESULTS.md.

## Remaining Limits

Real MDX and real DSL are unverified because no files were supplied. D-34
explicitly permits this outcome and carries real-file checks to Phase 8/user
dictionaries. Synthetic independent writers cover both formats including LZO
and Encrypted=2. Provider availability and quotas can change after these probes.

## Acceptance Checkpoint

No code/test failure remains. Confirm the Phase 2 CLI output and workflow using
02-UAT.md. Do not mark the phase accepted or advance until that response exists.
