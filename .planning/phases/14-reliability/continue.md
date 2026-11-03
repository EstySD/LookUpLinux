# Continue Phase 14

## Last action
Downloaded actual DSL English→Russian and ECDICT MDX English→Chinese directly and via configured proxy (HTTP 200, matching hashes); passed six source-article lookup checks per platform. DICT-06 is resolved. Target provider still reports blocked in six direct and six proxied cases; offline articles survive. Clone is off, proxy tunnel closed; no active jobs.

## Next action
Read 14-02-PLAN.md and provider-direct.json/provider-proxy.json. Resolve successful target provider availability and batch native second-monitor/borderless checks. Both actual network routes have been tried. Resolve the checkpoint automatically when the remaining availability blocker is addressed.

## Why
DICT-06 now has real source compatibility evidence in 14-01-SUMMARY.md. TRAN-07 still requires successful availability, rather than error handling. Phase 14 remains incomplete and Phase 15 depends on it.

## Open threads
- Provider google-gtx-marked-v1 reports blocked on both target routes; provider-direct.json/provider-proxy.json separate this from usable offline articles.
- Only one VM monitor is currently configured. Second-monitor and borderless checks remain pending, not failed product claims.
- Yomitan cold load measured ~4.4 seconds; no startup cache is claimed. Normal persistent-reader lookups work.
- Final Phase 13 batch has 865 tests on each host, zero failures/errors, with 11 Windows and 4 Linux skips; home-evidence includes native Wayland screenshot and second-launch focus proof.
- Product commits b1cf0b1 (Yomitan) and c92adcb (discoverable home). User lookup/ocr.py, tests/test_ocr_fallback.py and OMX changes remain uncommitted and preserved. Local validation logs/source.tar.gz are intentionally on disk, not all committed.

## Do not
- Do not invent acceptance or convert Yomitan into a purported real MDX/DSL source. Downloaded original DSL, MDX ZIP, source CSV and licenses are in ignored downloads/; public URL/hash receipts are retained.
- Do not control original arch-kde or its SSH2223. Only identity-guarded owned clone UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8, SSH2227 is authorized for these probes.
- Do not restart completed full suites on unchanged product code. Check manifests/reports first; no pending batch remains.
- Do not commit/revert the user's OCR/OMX edits.
