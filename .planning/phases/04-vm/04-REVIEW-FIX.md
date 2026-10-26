# Phase 4 review remediation

All three findings in 04-REVIEW.md are resolved; the original report is retained.

- CR-01: unbuffered os.read, bounded retained bytes, POSIX process-group cleanup
  and Windows process-tree cleanup avoid BufferedReader close-lock hangs. An
  outer-timeout regression launches an inherited-stdout grandchild and requires
  the probe to return privately within two seconds.
- CR-02: setup saves the per-run ownership snapshot before mutation, records
  launched identities, and rolls back failures. Host cleanup is attempted even
  if the setup response fails. Key release has an independent exception guard,
  preserving restore attempts and evidence writing. Injected registration,
  second-launch, lost-response and key-release failures verify these paths.
- CR-03: accepted() requires display, desktop, process and shortcut restoration,
  and rejects key-release/restoration errors. Each false flag has a regression.

Fresh evidence: 32 focused tests pass; full Windows 3.14/3.12 and Arch suites
each pass 528 tests. Final live harness returns zero with all restoration flags
true. Independent security verification reviewed the remediation and closed
14/14 threats. No screenshot/token/primary content is retained in evidence.
