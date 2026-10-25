---
phase: 03
status: verified
threats_open: 0
threats_total: 14
threats_closed: 14
asvs_level: 1
block_on: high
register_authored_at_plan_time: true
verified: 2026-10-25
---

# Phase 3 security verification

ASVS L1 presence/behavior audit against the three authored threat registers.
No broader security-proof claim. The secure-phase workflow permits direct
closure at L1 when the authored register has no unresolved mitigations.

| Threat | Mitigation and evidence | Disposition |
|---|---|---|
| T-03-01 | parse_tsv byte/row/text/shape/finite checks, Transform validation; tests.test_ocr malformed output/transform cases | Closed |
| T-03-02 | select_word retains rejected boxes, bounds nearest points; choose_query only DictSet.find; pure/CLI side-effect tests | Closed |
| T-03-03 | OcrError fixed reasons and suppressed contexts; quiet python -S imports | Closed |
| T-03-04 | _prepare_image regular file, pre-decode dimensions/file caps, prepared pixel cap, finite point checks; image resource tests | Closed |
| T-03-05 | constant tesseract argv, shell=False and PNG bytes stdin; invocation test | Closed |
| T-03-06 | subprocess.run timeout=3; stdlib kills/reaps expired child; TimeoutExpired mapping test | Closed |
| T-03-07 | QBuffer PNG, TSV stdout, captured stderr; fixed errors, control/bidi rejection, no output-file args; private errors/no-extra-image tests | Closed |
| T-03-08 | decoder internals transferred to target-distributed Qt/tesseract; application caps remain | Closed: plan transfer |
| T-03-09 | trusted local executable output buffers before 4MiB TSV check; capped prepared pixels | Closed: low-risk acceptance already authored in Plan 02 |
| T-03-10 | fixed public text, genuine Breeze style check, origin/version/layout metadata, non-skipped calibration; first fixture defects corrected before final gate | Closed |
| T-03-11 | finite strict point parser, image/point pairing and context rules; CLI usage tests | Closed |
| T-03-12 | rejection precedes dictionary/store/network, compounds offline, one final translate.lookup; actual SQLite count/context tests | Closed |
| T-03-13 | fixed Russian OCR errors; no raw path/process error on stderr; fixed-error and sentinel privacy tests | Closed |
| T-03-14 | CLI finally closes dictset and connection; recognition rejection before acquisition, legacy lifecycle tests remain green | Closed |

Fresh verification: 506 tests pass on both Windows interpreters and Arch;
target actual OCR CLI test runs all 96 cases without skips. Separate defaults
check passes 96/96. References: three SUMMARY files and calibration reports.

Accepted residual T-03-09 is not a streaming memory limit; a malicious/replaced
local tesseract executable is outside this single-user process-trust boundary.
Qt decoder and arbitrary desktop accuracy limits remain documented. No user
images or private desktop captures are in the committed fixture set.
