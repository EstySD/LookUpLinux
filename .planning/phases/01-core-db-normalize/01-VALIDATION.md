---
phase: 1
slug: core-db-normalize
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | stdlib `unittest` (Python 3.14; also run on 3.12) |
| **Config file** | none — discovery from project root (`tests/` package) |
| **Quick run command** | `python -m unittest tests.test_normalize tests.test_store tests.test_migrations -v` |
| **Full suite command** | `python -m unittest -v` |
| **Estimated runtime** | ~10 seconds (multiprocess tests dominate) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite must be green (Windows Python 3.14 + 3.12)
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

Filled by the planner/executor per task. Requirement → test map (from 01-RESEARCH.md §Validation Architecture):

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| DATA-02 / SC1 | `Running`, `run,`, `“Book’s”` → `running`, `run`, `book` | unit | `python -m unittest tests.test_normalize -v` | ❌ W0 | ⬜ pending |
| DATA-02 | quote/apostrophe fold table, soft hyphen, internal `'`/`-` kept | unit | same | ❌ W0 | ⬜ pending |
| DATA-02 / D-16 | possessive fixed point; contraction exceptions kept | unit | same | ❌ W0 | ⬜ pending |
| DATA-02 / D-04, D-17 | rejects: no Latin, Cyrillic/mixed, digits, len 1 except a/i | unit | same | ❌ W0 | ⬜ pending |
| DATA-02 / D-05 | phrases normalised, whitespace collapsed | unit | same | ❌ W0 | ⬜ pending |
| DATA-02 | idempotence fuzz (fixed seed, 20k) | property | same | ❌ W0 | ⬜ pending |
| DATA-01 / SC2 | two saves → one row, count 2, translation, context, first/last seen | unit | `python -m unittest tests.test_store -v` | ❌ W0 | ⬜ pending |
| DATA-01 / D-07, D-10 | empty context / None translation do not overwrite | unit | same | ❌ W0 | ⬜ pending |
| DATA-01 / D-12 | `RETURNING count` returns 1, 2, 3 | unit | same | ❌ W0 | ⬜ pending |
| Security | parameter binding (`'; DROP TABLE words; --` stored literally) | unit | same | ❌ W0 | ⬜ pending |
| DATA-01 / SC3 | 10 spawn writers, pre-created DB → count 10, no errors | integration | `python -m unittest tests.test_concurrency -v` | ❌ W0 | ⬜ pending |
| DATA-01 / SC3 / D-20 | 10 spawn writers on a **fresh** DB → no `database is locked` | integration | same | ❌ W0 | ⬜ pending |
| SC4 | DB created under non-existent data dir; reopen keeps rows; WAL | unit | `python -m unittest tests.test_migrations -v` | ❌ W0 | ⬜ pending |
| SC4 / D-14 | old-version DB migrated without losing words; `.bak-v1` exists | integration | same | ❌ W0 | ⬜ pending |
| SC4 / D-14 | newer DB refused, file bytes unchanged; failing step rolls back | unit | same | ❌ W0 | ⬜ pending |
| D-11 | path precedence `LOOKUP_DB` > `XDG_DATA_HOME` > `~/.local/share` | unit | `python -m unittest tests.test_paths -v` | ❌ W0 | ⬜ pending |
| D-15 | `lookup` imports stdlib only (no Qt) | unit | `python -m unittest tests.test_core_imports -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `lookup/__init__.py`, `lookup/normalize.py`, `lookup/store.py`
- [ ] spawn-safe worker module importable at top level (e.g. `tests/_workers.py`)
- [ ] `tests/__init__.py` and `tests/test_{normalize,store,migrations,concurrency,paths,core_imports}.py`
- [ ] Every test sets `LOOKUP_DB` / `XDG_DATA_HOME` to a temp path; connections closed before temp cleanup (Windows)
- [ ] Framework install: none (stdlib)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Default DB path on Arch is `~/.local/share/lookup/lookup.db` | SC4 | Real XDG env only in the VM | In the VM: `python -c "import lookup.store as s; print(s.default_db_path())"` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
