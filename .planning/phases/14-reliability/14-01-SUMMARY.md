---
phase: 14-reliability
plan: 01
requirements-completed: [DICT-06]
completed: 2026-11-03
---

# Real dictionary compatibility

User correctly challenged the absent download attempt. The previous missing-input blocker was premature: representative downloadable real dictionaries can satisfy this phase. Neither direct nor proxy downloads had been attempted previously.

Actual open-dsl-dict English→Russian Wikidict DSL (76,761,649 bytes, CC0) and published ECDICT headless MDX ZIP (73,065,884 bytes; English→Chinese) plus independent ECDICT source CSV were downloaded. Both explicit direct access and existing configured proxy returned HTTP 200 and identical SHA256 hashes for every file. Receipts: downloads/source-downloads-receipts.json. Source domains do not bypass proxy settings. Data and license notices stay in ignored downloads/; no dictionary redistribution.

Windows and owned Linux clone: six normal-lookup assertions each, all pass. DSL Africa/Japan/South America agree with published Russian source articles; MDX bank/cat/dog agree with Chinese translations in separately published CSV. Loaded 628,522 DSL entries and 3,402,564 MDX entries. Cold opens ~9.3/11.3 seconds on Windows and ~10.9/13.9 on Linux. These variants pass; no universal compatibility, warm-cache performance or Danila-file acceptance is claimed.

Evidence: source-batch-report.json, source-batch-manifest.json, host-real-dicts.json and target-real-dicts.json. First target attempt relied on a /tmp snapshot lost after reboot; fixed by staging a self-contained snapshot and rerunning affected target checks in one batch. Valid unchanged host results were reused. Product source matches the Phase 13 full-suite inventory, so full regressions were not repeated.

Target context provider was also tested with explicit direct transport and a temporary SSH reverse tunnel to the configured host proxy. Six blocked / zero successful cases on each route; offline_article_retained=true on both. TRAN-07 remains incomplete. source-cleanup.json confirms owned clone off and tunnel closed; original VM not controlled. Second-monitor and borderless acceptance remain pending.
