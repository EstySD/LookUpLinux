---
phase: 02
slug: offline-dicts-translate
status: verified
threats_open: 0
threats_total: 47
threats_closed: 47
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
created: 2026-10-25
---

# Phase 02 — Security

The eleven PLAN files contain 47 declared threats (T-02-01 through T-02-46,
plus T-02-SC). This audit checks those threats and the SUMMARY threat flags;
it does not claim exhaustive vulnerability discovery. The initial high-severity
redirect gap T-02-13 was fixed and verified before phase advancement.

## Trust Boundaries

| Boundary | Data crossing |
|---|---|
| Caller / OCR / dictionaries to SQLite | Lookup text, lemma, context, translation and cached provider payloads |
| Existing database to migration code | User schema, data and transaction state |
| Third-party dictionary files to codecs/readers | Compressed streams, sizes, offsets, checksums, encodings and markup |
| User configuration / environment to discovery and transport | Paths, dictionary identifiers, provider client names and online preference |
| Writable index cache to dictionary readers | JSON wrapper and format-specific index payload |
| Program to Google / MyMemory | Prepared lookup or context text, without identity/key/email parameters |
| Provider response to parser | Redirect locations, response bytes, JSON and failure responses |
| Worker thread to connection owner | Context result holder; SQLite connection remains on its owning thread |
| Program to terminal / logs | Requested result on stdout; fixed reasons and type names on stderr |
| Developer checkout to VM / repository | Test tree and dictionary data; personal text and real dictionary files excluded from commits |

## Threat Register

All rows preserve the severity and disposition declared in their source PLAN.
For accepted dispositions, the Accepted Risks Log records the existing plan
decision; the auditor has not newly accepted or downgraded any threat.

| Threat ID | Category | Component | Severity | Disposition | Mitigation / evidence | Status |
|---|---|---|---|---|---|---|
| T-02-01 | Tampering | SQL values / lemma | high | mitigate | Bound tuple in `lookup/store.py:203`, `lookup/translate.py:70`, `:81`, `:98`, `:103`; lemma injection regression in `tests/test_store.py` | closed |
| T-02-02 | Denial of service / data loss | v1→v2 migration | high | mitigate | Snapshot via SQLite backup `lookup/store.py:311`; lock/version recheck `:422`; authorizer `:443`; transactional version/commit `:453`; migration rollback/row-preservation tests in `tests/test_migrations.py` and `tests/test_store.py` | closed |
| T-02-03 | Information disclosure | Local translation cache | low | accept | AR-03; private creation helper `lookup/store.py:111` | closed |
| T-02-04 | Denial of service | LZO decode | high | mitigate | Declared length cap `lookup/lzo.py:28`; literal/match output checks `:46`, `:54`; lookbehind `:52`; hostile/truncation tests in `tests/test_lzo.py` | closed |
| T-02-05 | Denial of service | Dictzip geometry / inflate | high | mitigate | Header geometry `lookup/dictzip.py:99`; file-size and trailer geometry `:110`; bounded inflate `:132`; range/max_out `:148`; bomb tests in `tests/test_dictzip.py` | closed |
| T-02-06 | Denial of service | Truncated codecs | medium | mitigate | `lookup/lzo.py:36` converts IndexError; `_need` and header exception conversion `lookup/dictzip.py:24`, `:56`; truncation tests in both codec suites | closed |
| T-02-07 | Tampering | RIPEMD mistaken for security | low | accept | AR-07; compatibility-only module docstring in `lookup/ripemd128.py` | closed |
| T-02-SC | Tampering | Codec dependencies | low | accept | AR-SC; stdlib-only imports in `lookup/lzo.py`, `lookup/dictzip.py`, `lookup/ripemd128.py`; `tests/test_core_imports.py` | closed |
| T-02-08 | Tampering | Config values | high | mitigate | Config cap `lookup/config.py:86`; dictionary/type validation `:51`; client regex `:19`, `:78`; discovered-ID membership `lookup/dicts.py:418`; malformed config tests | closed |
| T-02-09 | Tampering / elevation | Index cache | high | mitigate | JSON wrapper save/load `lookup/dicts.py:171`, `:210`; bounded read `:216`; metadata/type comparisons `:225`; 0700/0600 atomic save `:191`; cache tampering and POSIX-mode tests | closed |
| T-02-10 | Tampering | Article markup / controls | medium | mitigate | `clean_text` removes Cc/Cf/Cs `lookup/dicts.py:87`; HTML parser drops script/style `:119`; plain-text conversion `:146`; control/bidi tests. Future Qt rendering is outside Phase 02 and must explicitly use plain text | closed |
| T-02-11 | Information disclosure | WordNet notice obligations | low | accept | AR-11; `lookup/data/NOTICE-wordnet.txt`, checked by `tests/test_irregular_data.py` | closed |
| T-02-12 | Information disclosure | Query in transport errors | high | mitigate | Fixed `TranslateError` reasons `lookup/online.py:35`; `_fail` uses `from None` `:226`; transport catches `:255`; sentinel checks `tests/test_privacy.py:40` | closed |
| T-02-13 | Spoofing | Cross-host / downgraded redirects | high | mitigate | `_NoRedirect` rejects all follow-ups before dispatch; `_fetch` uses its own opener. `FetchTests.test_redirects_never_send_a_second_request` exercises actual urllib redirect handling for 301/302/303/307/308 and asserts only the initial request occurs for foreign-host, HTTP downgrade and same-host targets | closed |
| T-02-14 | Denial of service | Slow / oversized network body | medium | mitigate | Shared deadline `lookup/online.py:320`; per-attempt remaining timeout `:275`, `:288`; 16 KiB reads and 1 MiB cap `:246`; wall-clock checks `:252`; cap/deadline tests | closed |
| T-02-15 | Tampering | Hostile provider JSON | medium | mitigate | Safe nested indexing `lookup/online.py:119`; decode/type guards `:130`, `:150`, `:201`; parts/terms limits `:170`; malformed JSON and shape tests in `tests/test_online.py` | closed |
| T-02-16 | Information disclosure | Provider identity parameters | medium | mitigate | MyMemory URL contains only q/langpair `lookup/online.py:286`; `tests/test_online.py:500` | closed |
| T-02-17 | Tampering | Client query injection | medium | mitigate | Client regex/fullmatch `lookup/online.py:221`, `:312`; URL encoding `:271`; sanitization tests `tests/test_online.py:455` | closed |
| T-02-18 | Denial of service / tampering | StarDict offsets / lengths | high | mitigate | Entry validation before data reads `lookup/stardict.py:119`; `MAX_ARTICLE_BYTES` and true data length; skipped-entry tests in `tests/test_stardict.py` | closed |
| T-02-19 | Denial of service | Huge StarDict index / syn | high | mitigate | Bounded index/gzip reads `lookup/stardict.py:81`; ifo cap `:46`; syn read capped at MAX_IDX_BYTES `:95`. Syn is truncated to cap rather than oversized-file rejection; the declared memory bound is present | closed |
| T-02-20 | Denial of service | Mueller regex work | medium | mitigate | Scan and pointer windows `lookup/stardict.py:130`, `:178`; bounded senses and hostile timing tests in `tests/test_stardict.py` | closed |
| T-02-21 | Tampering | StarDict HTML-like fields | medium | mitigate | x/h/g/k handled by `html_to_text` `lookup/stardict.py:280`; final `clean_text` `:287`; field conversion tests | closed |
| T-02-22 | Denial of service | DSL optional headwords | high | mitigate | `MAX_VARIANTS=32` `lookup/dsl.py:32`; cap applied during expansion `:85`; optional-group tests in `tests/test_dsl.py` | closed |
| T-02-23 | Denial of service | DSL size / nested tags | medium | mitigate | File cap `lookup/dsl.py:552`; article bound `:119`; markup/text caps `:243`; iterative converter and hostile timing tests | closed |
| T-02-24 | Tampering | DSL article markup | medium | mitigate | Converter strips tags, then `clean_text` `lookup/dsl.py:410`, `:433`, `:444`; unknown-tag/control tests | closed |
| T-02-25 | Tampering | DSL cache ranges | medium | mitigate | `_valid_payload` checks entry types, ranges and key targets `lookup/dsl.py:200`; invalid cache rebuild `:557`; eleven tampering cases in `tests/test_dsl.py` | closed |
| T-02-26 | Denial of service | MDX compressed blocks | high | mitigate | Size check before decode `lookup/mdx.py:84`; bounded LZO `:95`, zlib `:100`; exact decoded length `:102`; bomb/oversize tests | closed |
| T-02-27 | Denial of service / tampering | MDX tables / counts | high | mitigate | Header bound `lookup/mdx.py:146`; block/entry/info caps `:271`; aggregate key cap `:297`; record bounds `:306`; open exception conversion `:581`; hostile structure tests | closed |
| T-02-28 | Tampering | MDX checksums | medium | mitigate | Block Adler-32 `lookup/mdx.py:107`; header `:152`; keyword header `:259`; checksum tests in `tests/test_mdx.py` | closed |
| T-02-29 | Denial of service | MDX link cycles | medium | mitigate | Visited set / MAX_LINK_HOPS `lookup/mdx.py:475`, `:481`; loop/missing-target/long-chain tests | closed |
| T-02-30 | Information disclosure | Registration-encrypted MDX | low | accept | AR-30; fixed `encrypted_registration` refusal `lookup/mdx.py:176` | closed |
| T-02-31 | Tampering / information disclosure | Config traversal / discovery | high | mitigate | Non-following walk and symlink pruning `lookup/dicts.py:278`, `:282`, `:286`; IDs matched against discovered paths `:415`; hostile-ID and symlink tests | closed |
| T-02-32 | Denial of service | Dictionary directory traversal | medium | mitigate | `MAX_WALK_DEPTH=6`, `MAX_DISCOVERED=200` `lookup/dicts.py:239`; hidden/depth pruning `:282`; candidate cap `:304`; patched-cap test | closed |
| T-02-33 | Denial of service | One corrupt reader | medium | mitigate | Per-reader lookup/has catches `lookup/dicts.py:327`, `:341`; per-open fixed error mapping `:436`; failure-isolation tests in `tests/test_dicts.py` | closed |
| T-02-34 | Tampering | LOOKUP_DICTS override | low | accept | AR-34; explicit env hook `lookup/dicts.py:262` | closed |
| T-02-35 | Information disclosure | Excess online text / offline mode | high | mitigate | Dictionary-hit fallback guard `lookup/translate.py:189`; context requires online `:163`; prepared context `:164`; online truncation `lookup/online.py:309`; CLI online/offline choice `lookup/__main__.py`; zero-call offline/dictionary tests | closed |
| T-02-36 | Tampering | Cache / meta SQL | high | mitigate | Bound values in `lookup/translate.py:70`, `:81`, `:89`, `:98`, `:103`; quote/semicolon tests `tests/test_translate.py:110` | closed |
| T-02-37 | Tampering | Poisoned cached payload | medium | mitigate | Strict result shape/type validation `lookup/online.py:68`; invalid JSON/cache miss `lookup/translate.py:69`; malformed payload tests | closed |
| T-02-38 | Denial of service | Context worker / blocked join | medium | mitigate | Holder-only boundary `lookup/translate.py:124`; daemon thread `:173`; join bounded by elapsed budget `:218`; owner-thread and hung-worker tests | closed |
| T-02-39 | Information disclosure | Query in orchestration logging | high | mitigate | Fixed reason assignment `lookup/translate.py:202`, `:225`; no logging/printing per AST test `tests/test_privacy.py:23`; behavioral sentinel test `:40` | closed |
| T-02-40 | Information disclosure | CLI stderr / traceback | high | mitigate | Fixed/type-name warnings and catch-all `lookup/__main__.py:107`, `:120`, `:135`; expected validation error at :118 uses internal fixed messages; CLI sentinel test `tests/test_privacy.py:76` | closed |
| T-02-41 | Information disclosure | Library print/log calls | high | mitigate | AST scans every lookup library module `tests/test_privacy.py:23`, covers print/logging/warnings/stdout/stderr writes | closed |
| T-02-42 | Denial of service | Long local input | low | accept | AR-42; online cap `lookup/online.py:103`; linear classification `lookup/translate.py:31` | closed |
| T-02-43 | Tampering | LOOKUP_* path overrides | low | accept | AR-43; explicit path hooks `lookup/config.py:32`, `:42`, `lookup/dicts.py:262`, `lookup/store.py:80` | closed |
| T-02-44 | Information disclosure / licensing | Real dictionaries in Git | medium | mitigate | Fresh `git ls-files` for db/sqlite/mdx/dsl/dz/ifo/idx/dict/tar.bz2 returned no files; `.gitignore` excludes databases; `02-VM-RESULTS.md` records scp to VM-only directory | closed |
| T-02-45 | Information disclosure | UAT network text | low | accept | AR-45; fixed words and pangram documented in `02-VM-RESULTS.md` | closed |
| T-02-46 | Tampering | Real dictionary trials | medium | accept | AR-46; hostile fixture suites in `tests/test_stardict.py`, `tests/test_dsl.py`, `tests/test_mdx.py`; actual Mueller checks recorded; real MDX/DSL explicitly unverified | closed |

## Initial Finding: T-02-13 (resolved)

Resolution: fixed provider URLs now reject all redirects via `_NoRedirect`.
The regression uses real urllib handlers with an in-memory HTTPS transport;
no disallowed request occurs. All 483 tests pass on Windows 3.14/3.12 and
Arch 3.14.8; a live Google gtx probe still returns `бегать` for `run`.
The original finding below is retained as audit history.

`lookup/online.py:238` opens a request with urllib's default redirect handler.
urllib follows HTTP redirects before `urlopen` returns its final response.
The scheme/host comparison at lines 239–241 therefore detects an untrusted
destination after the new request has already been transmitted. A provider
response with a Location URL on another host, or with HTTP, can cause a
request carrying lookup text to that destination before `bad_response` is
returned. Verified TLS on the initial connection does not enforce the
declared destination restriction for subsequent requests.

The same residual is explicitly recorded in `02-04-SUMMARY.md` under Threat
Flags. It was not declared accepted in the plan and cannot be closed by
that note. Existing tests at `tests/test_online.py:379` and `:384` provide a
fake final response URL; they demonstrate post-response rejection, not
pre-request prevention.

**Required remediation:** reject redirects before following them, or install
a redirect handler that validates scheme, host and destination policy
before issuing the next request. Keep default TLS certificate validation.
Add a transport-level regression which exercises urllib's redirect machinery
and asserts that no request reaches a disallowed host or downgraded URL.

## Accepted Risks Log

These are transcriptions of **pre-existing `accept` dispositions in the
numbered PLAN files**, not fresh auditor risk acceptance. Acceptance provenance
is the cited authored plan; no human acceptance or additional user testing is
claimed by this audit.

| Risk ID | Threat Ref | Existing plan rationale | Decision source |
|---|---|---|---|
| AR-03 | T-02-03 | Local persistent translations share the existing private SQLite file; no new remote disclosure | 02-01-PLAN.md |
| AR-07 | T-02-07 | RIPEMD-128 derives MDX compatibility keys only; it is not a security primitive | 02-02-PLAN.md |
| AR-SC | T-02-SC | Stdlib codecs avoid new package-manager dependencies | 02-02-PLAN.md |
| AR-11 | T-02-11 | WordNet notice is shipped and Princeton is not used for promotion | 02-03-PLAN.md |
| AR-30 | T-02-30 | Registration encryption is unsupported and fails with a fixed reason | 02-07-PLAN.md |
| AR-34 | T-02-34 | The user's own dictionary-path environment override is an intentional test/config hook | 02-08-PLAN.md |
| AR-42 | T-02-42 | Local single-user input handling is linear; online text is capped | 02-10-PLAN.md |
| AR-43 | T-02-43 | LOOKUP_* are intentional user-controlled path overrides | 02-10-PLAN.md |
| AR-45 | T-02-45 | UAT sends fixed test words and a pangram only | 02-11-PLAN.md |
| AR-46 | T-02-46 | Hardened readers are tested with real supplied data; defects require regression fixes; absent MDX/DSL samples remain unverified | 02-11-PLAN.md |

## Summary Threat Flags

Read all eleven SUMMARY files. Numbered Threat Flags sections in 01–07 map
to declared T-02 threats. The redirect note in 02-04-SUMMARY mapped to
T-02-13, now resolved by the follow-up fix. No unregistered flag was found.
Plans 08–11 do not add an unmapped threat flag.

## Validation and Limits

- Inspected the implemented control locations above, not only summaries.
- Parent reported a fresh full run: 482 unittest tests, OK, six skips. This
  auditor did not independently rerun that full suite or the historical VM
  checks and does not claim new VM evidence.
- Fresh repository tracked-file check found no real dictionary/database
  artifacts matching the listed extensions.
- ASVS L1 is a presence check, not a complete security proof. POSIX file modes
  cannot be validated behaviorally on this Windows host; implementation and
  existing POSIX-specific tests are present.
- Future Qt rendering must preserve the plain-text boundary established here.
- Synonym reading preserves the cap but truncates rather than rejects an
  oversized syn file; this is a bounded-read implementation variance, not an
  unbounded allocation.

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open blocking | Open non-blocking | Run By |
|---|---|---|---|---|---|
| 2026-10-25 | 47 | 46 | 1 | 0 | Codex security auditor |
| 2026-10-25 | 47 | 47 | 0 | 0 | Codex host: remediation and ASVS L1 recheck |

## Sign-Off

- [x] Every declared threat has a disposition and evidence or explicit gap.
- [x] Previously accepted plan risks recorded with source provenance.
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set.

**Approval:** verified after T-02-13 remediation and fresh behavioral tests.
