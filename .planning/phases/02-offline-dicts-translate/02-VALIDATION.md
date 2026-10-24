---
phase: 2
slug: offline-dicts-translate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-24
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: 02-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | stdlib `unittest` (Phase 1 convention: `tests/` package, `tests/_support.py`) |
| **Config file** | none (discovery from repo root) |
| **Quick run command** | `python -m unittest tests.test_lzo tests.test_ripemd128 tests.test_stardict tests.test_dsl tests.test_mdx tests.test_dicts tests.test_lemma tests.test_online tests.test_translate tests.test_cli` |
| **Full suite command** | `python -m unittest` |
| **Other interpreters** | `py -3.12 -m unittest` (Windows host); `ssh archvm 'cd ~/LookUpLinux && python3 -m unittest'` (VM, 3.14) |
| **Estimated runtime** | ~30 seconds (fixtures only, no network, no real dictionaries) |

---

## Sampling Rate

- **After every task commit:** Run the quick run command (tests touched by the task at minimum)
- **After every plan wave:** Run `python -m unittest` on 3.14 and `py -3.12 -m unittest`
- **Before `/gsd-verify-work`:** Full suite green on 3.14 and 3.12; VM run on 3.14; manual SC4 and Mueller 7 checks recorded
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

Requirement-level map (task IDs are filled in by the planner in each PLAN.md `<verify>` block):

| Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|-------------|----------|-----------|-------------------|-------------|--------|
| TRAN-01 | StarDict parse, `sametypesequence`, 32/64-bit idx, invalid entries skipped, dictzip random read | unit | `python -m unittest tests.test_stardict` | ❌ W0 | ⬜ pending |
| TRAN-01 | DSL: UTF-16LE/UTF-8 BOM, headword groups, `{}` expansion, escapes, tags | unit | `python -m unittest tests.test_dsl` | ❌ W0 | ⬜ pending |
| TRAN-01 | MDX v1.2/v2.0, zlib/none/LZO, Encrypted=2, Adler-32 mismatch = error | unit | `python -m unittest tests.test_mdx tests.test_lzo tests.test_ripemd128` | ❌ W0 | ⬜ pending |
| TRAN-01 | Discovery, order, enabled flags, skip reasons (`Encrypted=1`, broken files) | unit | `python -m unittest tests.test_dicts` | ❌ W0 | ⬜ pending |
| TRAN-01 | Real Mueller 7: `run` gives transcription + POS senses | integration (skipped unless `LOOKUP_TEST_DICTS`) | `python -m unittest tests.test_mueller_sample` | ❌ W0 | ⬜ pending |
| TRAN-02 | Google parse from fixtures; 429 HTML → `blocked`; non-JSON → `bad_response`; no `d[1]` for word → `not_found` | unit | `python -m unittest tests.test_online` | ❌ W0 | ⬜ pending |
| TRAN-02 | ~3 s shared deadline across clients/providers (fake clock/transport) | unit | `python -m unittest tests.test_online` | ❌ W0 | ⬜ pending |
| TRAN-02 | MyMemory only for phrases/sentences; word → `not_found` | unit | `python -m unittest tests.test_online` | ❌ W0 | ⬜ pending |
| TRAN-03 | Repeat lookup answered from cache with network forbidden; errors not cached; sentence cache ≤1000 | unit | `python -m unittest tests.test_translate` | ❌ W0 | ⬜ pending |
| TRAN-04 | `running`, `ran`, `went`, `men`, `books`, `stopped`, `boxes`, `better`, `news` → expected article/lemma; pointer follow | unit | `python -m unittest tests.test_lemma` | ❌ W0 | ⬜ pending |
| TRAN-05 | Sentence translated in parallel; offline/error → result without sentence translation | unit | `python -m unittest tests.test_translate` | ❌ W0 | ⬜ pending |
| DATA-03 | 2–4 words saved once; >4 not saved; no network + no dict hit → saved with NULL translation; online not_found → not saved | unit | `python -m unittest tests.test_translate` | ❌ W0 | ⬜ pending |
| D-25 | CLI exit codes 0/1/2, `--list-dicts`, UTF-8 output | CLI subprocess | `python -m unittest tests.test_cli` | ❌ W0 | ⬜ pending |
| D-26 | Library modules print/log nothing | unit | `python -m unittest tests.test_privacy` | ❌ W0 | ⬜ pending |
| Phase 1 | Core stays stdlib-only, Qt-free (new modules added) | unit | `python -m unittest tests.test_core_imports` | ✅ extend | ⬜ pending |
| Phase 1 | Migration v2 coexists with Phase 1 tests (`V1 = MIGRATIONS[:1]`) | unit | `python -m unittest tests.test_migrations tests.test_store tests.test_concurrency` | ✅ update | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/gtx/` — captured Google JSON (word run/ran/books/news, phrase, sentence, non-word) from the research scratchpad `fx/`
- [ ] `tests/fixtures/mymemory/` — `run`, `break out`, sentence, `xyzzyq`
- [ ] `tests/fixtures/lzo/vectors.json` — liblzo2-generated vectors (≤ ~8 KB payloads)
- [ ] `tests/_writers.py` — test-only writers for StarDict, DSL, MDX (v1.2/v2.0, zlib/none/LZO, Encrypted=2)
- [ ] `tests/_support.py` — `V1 = MIGRATIONS[:1]`, transport that fails the test on any network call
- [ ] `tests/test_mueller_sample.py` — skipped unless `LOOKUP_TEST_DICTS` is set; archive never committed

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Online path reachable from VM network via the app's `urllib`; failure reason shown | TRAN-02 (SC4) | Real network | In VM: `python3 -m lookup --word xyzzyq`; `python3 -m lookup --text "The quick brown fox jumps over the lazy dog."`; disconnect network → reason shown within ~3 s |
| Real Mueller 7 StarDict | TRAN-01, TRAN-04 | Real file/encoding | Put `mueller7.ifo/.idx.gz/.dict.dz` in `~/.local/share/lookup/dicts/mueller7/`; `--list-dicts` (46 231 entries, 1 skipped); `--word run`, `--word ran` |
| Real MDX file | TRAN-01 | No sample available | Denis drops a `.mdx` into the dicts folder; `--list-dicts` + `--word`; if none supplied → mark unverified, not failed |
| Timing D-09 | TRAN-01 | VM timing | `LOOKUP_TIMING=1 python3 -m lookup --word run --offline` ×10 in VM; warm open ≤ 300 ms, search ≤ 20 ms |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
