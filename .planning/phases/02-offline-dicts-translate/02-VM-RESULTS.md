# Phase 2 VM Verification Results

Observed 2026-10-25, committed application revision `e92a26a`.

## Environment

- Windows host: Python 3.14 and Python 3.12, stdlib unittest.
- Target: `ssh archvm`, VirtualBox Arch Linux, Python 3.14.8.
- Archived the committed tree with `git archive --format=tar HEAD`, copied via
  scp, extracted into `~/LookUpLinux-gsd-e92a26a`. The pre-existing
  `~/LookUpLinux` was preserved rather than recursively deleted.
- All application checks ran from that checkout. No packages were installed.
- Only `mueller7.ifo`, `mueller7.idx.gz`, `mueller7.dict.dz` were copied to
  `~/.local/share/lookup/dicts/mueller7/`. No dictionary data entered Git.
- The UAT harness used `tempfile.TemporaryDirectory(prefix='lookup-phase02-uat-')`
  with separate LOOKUP_DB, LOOKUP_CACHE, LOOKUP_CONFIG and empty dictionary roots.
  Its context manager removed the throwaway databases/cache after the run.

## Test suites

| Environment | Command | Count | Skipped | Time | Result |
|---|---|---:|---:|---:|---|
| Windows 3.14 | `python -m unittest` | 482 | 6 | 20.583 s | OK |
| Windows 3.12 | `py -3.12 -m unittest` | 482 | 6 | 20.045 s | OK |
| Arch VM 3.14.8 | `python3 -m unittest` | 482 | 2 | 10.801 s | OK |
| VM real Mueller | `LOOKUP_TEST_DICTS=$HOME/.local/share/lookup/dicts python3 -m unittest tests.test_mueller_sample -v` | 2 | 0 | 0.152 s | OK |

The VM full suite ran the POSIX file-mode and symlink checks skipped on Windows.
Its two skips were the opt-in real Mueller tests, then run separately without skips.
The suite command captured its exit status before displaying the final log lines.

## Mueller 7 checks

`python3 -m lookup --list-dicts`: exit 0, name `mueller`, format `stardict`,
id `mueller7/mueller7.ifo`, entries **46231**, skipped **1**, status **ok**.

Ran `python3 -m lookup --word WORD --offline --no-save` for each row:

| Input | Headword shown | Lemma | Exit |
|---|---|---|---:|
| run | run, IPA rʌn, n/v senses and full article | none | 0 |
| ran | run, header `ran → run` | run | 0 |
| running | running, own article | run | 0 |
| men | man | man | 0 |
| went | go | go | 0 |
| books | book | book | 0 |
| stopped | stop | stop | 0 |
| boxes | box | box | 0 |
| runs | run | run | 0 |
| better | better, own article | none | 0 |
| news | news, own article | none | 0 |
| break out | not found; online disabled | none | 1 |

The earlier context's claim that `break out` is a Mueller headword was corrected
by the phase research; actual headword-only lookup confirms absence.

`curl -sI --max-time 15 https://qstardict.ylsoftware.com/files/mueller7.tar.bz2`
from the VM returned **HTTP 200 OK**, **Content-Length: 4771569** (A6).

## Timing (D-09)

Ten new CLI processes, same warm dictionary/cache, each running
`LOOKUP_TIMING=1 python3 -m lookup --word run --offline --no-save`.
Stage values parsed from the single stderr `timing:` line, in milliseconds:

| Stage | VM median | VM maximum | Target | Result |
|---|---:|---:|---:|---|
| open_dicts | 91.0515 | 110.784 | ≤300 | within budget |
| dicts | 4.8395 | 7.708 | ≤20 | within budget |

Raw open_dicts: 98.091, 108.783, 97.931, 110.784, 86.670, 89.858,
92.245, 88.145, 88.709, 83.693.
Raw dicts: 7.591, 4.800, 4.584, 4.626, 4.749, 6.732, 5.588, 4.879,
7.708, 4.684.

Windows comparison, one run against the same Mueller files:
open_dicts **95.682 ms**, dicts **4.898 ms**, open_db **32.647 ms**,
total **133.354 ms**. No stage missed its target; no profiling was needed.
These numbers cover Mueller only, not all future user dictionaries.

## Online from the VM (SC4)

Probed the application's own urllib path, not curl. For each Google client,
called `online.google_translate('run', 'word', client, start+3, time.monotonic)`.
For MyMemory called `online.mymemory_translate(pangram, 'sentence', start+3,
time.monotonic)`. Only fixed test text was sent.

| Provider/client | Result | Elapsed ms |
|---|---|---:|
| Google gtx | ok, бегать | 217.23 |
| Google dict-chrome-ex | ok, бегать | 123.89 |
| Google at | ok, бегать | 204.58 |
| MyMemory | ok, Russian sentence | 434.09 |

With LOOKUP_DICTS pointing to an empty directory, LOOKUP_TIMING=1 and a fresh DB:

| Command suffix to `python3 -m lookup` | Observed result |
|---|---|
| `--word run --no-save` | Exit 0; Google gtx translation, IPA and POS; online 141.968 ms |
| `--word run` twice | Both cache hits; online 0.000 ms; counts 1 then 2 |
| `--word xyzzyq` | Exit 1, Не найдено.; no words row |
| `--text "The quick brown fox jumps over the lazy dog."` | Exit 0, Russian sentence; no words row |
| `--word "break out"` | Exit 0, online translation; one phrase row, count 1 |
| `--text "one two three four five"` | Exit 0; translation, no words row |

SQL `SELECT word,count,translation FROM words ORDER BY word` returned only
`break out` (count 1) and `run` (count 2); neither sentence nor non-word was saved.

Failure simulation: set both `https_proxy` and `HTTPS_PROXY`, clear `no_proxy`
and `NO_PROXY`, use separate fresh databases for each proxy and the real Mueller
directory. The measured times include interpreter start and dictionary open.

| Proxy | CLI query | Result | Wall ms |
|---|---|---|---:|
| 127.0.0.1:9 refused | `--word run --context "I run fast every day."` | Exit 0, article preserved; context: нет сети | 206.54 |
| 127.0.0.1:9 refused | `--word zzqx` | Exit 1; нет сети | 233.43 |
| 10.255.255.1:3128 blackhole | `--word run --context "I run fast every day."` | Exit 0, article preserved; context timeout | 3194.61 |
| 10.255.255.1:3128 blackhole | `--word zzqx` | Exit 1; timeout | 3175.70 |
| refused | `--word zzqx --offline` | Exit 1, online disabled | 221.95 |
| blackhole | `--word zzqx --offline` | Exit 1, online disabled | 203.63 |

Both blackhole runs stayed below the approximately 3.5 s acceptance budget.
Offline network avoidance is additionally proven with forbidden urllib in tests.

## Second provider decision

All three Google clients currently work through urllib from this VM; the older
concern about gtx being blocked was not reproduced. Keep MyMemory as the already
implemented independent fallback for phrases and sentences. It also answered
the live probe. It is not used for single words because it cannot distinguish
unknown words reliably (D-31). No keyed Cloud Translation escalation is needed
from this evidence; future availability and quotas remain external constraints.

## Real MDX / DSL

`find ~/.local/share/lookup/dicts` found no MDX or DSL files.

- Real MDX: unverified (no file supplied).
- Real DSL: unverified (no file supplied).

Synthetic independent writers cover MDX v1.2/v2.0, zlib, LZO and Encrypted=2,
and DSL UTF-8/UTF-16 and dictzip. Real-file compatibility remains open for the
user's dictionaries and Phase 8; this is unverified rather than a failure (D-34).

## Defects found and fixed

- Plan 10 privacy tests identified missing explicit context suppression on the
  final online-provider error. `raise TranslateError(reason) from None` fixes
  it; tests assert no text in output/logs, reason-only exceptions and suppression.
- No additional Windows 3.12 or VM-only defects appeared.

## Notes for Phase 7 and Phase 8

- Mueller source is reachable: HTTP 200, archive size 4771569 bytes.
- PKGBUILD must ship `lookup/data/irregular.txt` and `NOTICE-wordnet.txt`.
- LOOKUP_DB, LOOKUP_DICTS, LOOKUP_CONFIG, LOOKUP_CACHE and LOOKUP_TIMING are
  available for tests and diagnostics; LOOKUP_TEST_DICTS enables real samples.
- Mueller timing meets D-09; measure the combined cost of actual user
  dictionaries later. The DSL 200000-article cold/warm concern remains separate.
- The Phase 5 daemon should retain DictSet and the connection, and reopen the
  database after upgrades/migrations (Phase 1 schema-version note).
- Free providers may change availability/quotas. Current VM evidence supports
  all Google clients and the phrase/sentence MyMemory fallback.
- Real MDX and DSL checks remain open for Phase 8 or supplied user files.
