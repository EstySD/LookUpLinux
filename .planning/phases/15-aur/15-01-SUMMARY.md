---
phase: 15-aur
plan: 01
requirements-completed: [PUB-02]
completed: 2026-11-03
---

# Public package and release preparation

Public 0.2.1 source includes native KWin plugin build inputs and excludes private workspace/AUR self-referencing metadata. Exact-source AUR PKGBUILD and native makepkg-generated .SRCINFO agree. Public package excludes Mueller and preserves project/helper/WordNet notices.

Final batch: release-1793725749, command `python .planning/phases/15-aur/run_release_batch.py`. Host and Linux each ran 877 tests with zero failures/errors (13/22 skips). Initial target run found one timing-sensitive GUI test with a fixed 90 ms wait; reuse of its existing bounded dismissal helper fixes the test without changing product behavior. All independent results were collected before that repair.

Actual owned-clone gates pass: normal-user makepkg build, package contents/licenses, clean installed offline lookup, upgrade from the genuine 0.1.0 package retaining words/cards/settings, and removal retaining user data. Final 0.2.1 package is reinstalled; VM remains running. No original VM controls were used. Authoritative hashes and reports: 15-ACCEPTANCE.json and release-1793725749/package-report.json.

Denis explicitly reported finishing manual VM tests, committed OCR and popup fixes and authorized GitHub publication/milestone completion. This supersedes the prior no-publication/manual-use checkpoint. Existing agent evidence remains labelled agent; no detailed human scenario results are invented. AUR submission is still separate.
