---
phase: 04-vm
reviewed: 2026-10-26T04:24:35Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - lookup/platform.py
  - lookup/capture.py
  - lookup/ocr.py
  - tools/vm_spike.py
  - tools/check_vm_spike.py
  - tools/lookup-vm-spike.desktop.in
  - tests/test_platform.py
  - tests/test_vm_spike.py
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: resolved
unresolved: 0
---

# Phase 4 code review

All three findings below have been remediated and regression-tested. See
04-REVIEW-FIX.md and the independent 04-SECURITY.md; original findings remain
as review history.

Targeted review of actual implementation, relevant plans/context and tests.
The current live result records successful restoration on its observed path;
the defects below concern failure handling and acceptance of future runs.
No VM action, source modification or result-file rewrite was performed.

## CR-01 — BLOCKER: subprocess cleanup can exceed its deadline indefinitely

**File:** `lookup/platform.py:55`–`:56`.

The reader uses BufferedReader.read(limit+1). If a child launches a descendant
which inherits stdout, killing/waiting for only the immediate child does not
produce EOF. After reader.join(1) times out, child.stdout.close() waits on the
reader's internal I/O lock, so run() does not return within its deadline.

**Local reproduction:** An outer Python process invokes run() with timeout=.05
on a Python child which starts another Python process sleeping four seconds
and then sleeps itself. The grandchild inherits stdout. An independent outer
subprocess timeout at two seconds expires: run(timeout=.05) has not returned.
The same situation can persist indefinitely for a persistent descendant.

**Fix:** Make read cancellation independent of EOF and avoid closing a buffered
stream while another thread owns its read lock. On the POSIX target, bounded
nonblocking/select reads are a suitable small implementation; alternatively
isolate and terminate the child process group and ensure descendants cannot
retain the read endpoint. Preserve the byte cap and child reaping. Add an
inherited-stdout descendant regression with an outer timeout guard.

## CR-02 — BLOCKER: partial setup and key-release failures bypass rollback

**File:** `tools/check_vm_spike.py:77`–`:83`, `:190`–`:192`, `:244`–`:245`.

Target setup writes snapshot.json and the desktop entry, runs kbuildsycoca6,
then starts fixture/owner processes. The host sets setup=True only after the
entire remote setup succeeds. Any error after the first mutation, such as a
kbuildsycoca6 failure or failed process launch, leaves setup=False and skips
remote('finish'). The desktop/shortcut and possibly a fixture process remain.
In addition, an exception from keys() at the start of finally prevents every
subsequent rollback/result-write action.

**Fix:** Make setup transactional on the target: retain ownership metadata and
perform idempotent owned cleanup on any post-snapshot error. Ensure host
cleanup is attempted after a setup request even if its response fails, while
refusing to clean an unrelated prior snapshot. Guard key release independently
so its failure cannot suppress remote rollback or evidence writing. Record
owned process IDs as they are launched so a process without a registered bus
service can still be cleaned. Add mocked failures after desktop registration,
between child launches, and during final key release.

## CR-03 — BLOCKER: gate runner reports success when desktop restoration fails

**File:** `tools/check_vm_spike.py:251`.

The exit predicate checks display_restored only. A result with no error,
required_remaining=[], and restoration={display_restored:true,
desktop_restored:false} returns zero. That accepts a failed required cleanup
gate, contrary to Plan 03's restoration contract. The current successful run's
desktop_restored=true does not remove this false-pass path.

**Fix:** Require every mandatory restoration flag, including desktop_restored,
and reject restoration_error explicitly. Test a successful display restoration
with a failed desktop restoration and require a nonzero exit. Share the final
gate predicate with the unit test rather than relying on the live happy path.

---

The OCR bytes extension preserves bounded QBuffer lifetime and resets image
DPR before physical-pixel operations. No additional concrete defect was found
in that extension, raw channel-layout conversion, desktop Exec quoting, or
owned-window command validation during this targeted pass. This is not a
claim that all possible input or compositor behavior was tested.
