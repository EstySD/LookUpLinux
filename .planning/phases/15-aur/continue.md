# Continue Phase 15

## Current state

Phase 14 is complete in commit 1e6e025, including live provider fallback and native two-monitor/borderless evidence. Phase 15 is partially implemented; do not create a completion summary or mark PUB-02 accepted yet.

Prepared 0.2.1 only. User explicitly forbids publication. No push, remote draft/release, workflow dispatch, tag push or AUR submission was performed.

Host full suite: 870 tests, zero failures/errors, 11 skips. Logs/source identity: host-full.log, host-batch-manifest.json, host-batch-report.json. No validation jobs remain active. The public source archive now includes the native KWin build inputs. tools/stage_aur.py generated the recipe; native makepkg --printsrcinfo exit 0 generated .SRCINFO without interacting with the desktop.

Artifacts: dist/lookup-linux-0.2.1-source.tar.gz, dist/lookup-linux-0.2.1-archlinux-x86_64-build-kit.tar.gz, dist/SHA256SUMS, aur/AUR.json, aur/PKGBUILD and aur/.SRCINFO. Generated recipe/metadata are also in packaging/aur. Source SHA256: 7cdbd750e1a089debb86819fd6284ecc1ac2b269fe9e5d11285a9d72f8dbbafd. AUR metadata intentionally stays outside the source archive to avoid checksum self-reference.

## Visible manual preview — leave running

User then requested a normal GUI VM, not headless. Owned clone lookup-gsd-07 is running with SessionName=GUI/Qt. Current product was staged from actual worktree sources into /home/lookup07/lookup-preview-0.2.1-1793721877/lookup-source and launched as lookup07 with python -m lookup --app. This is the latest source preview, not a claimed installed 0.2.1 package. Source SHA256: a7c77136188f5a048d55caed72e1183eaaf52bb8c7294f9458025b89ca09fca0. Effective shortcut is Meta+Shift+E. manual-preview-screen.png confirms the home window was visibly displayed; manual-preview-job.json contains PID/path/log. Initial optional Open probe used the wrong DBus path after a successful --app launch; the helper is corrected to /Lookup. The visible launch itself succeeded. Do not restart the app to repeat that optional probe while Denis tests.

Do not apply the old automatic poweroff cleanup while this explicit user request is active. Do not automate GUI input or package install/removal during the manual session. Metadata-only SSH commands used arch's separate directory and did not alter the GUI/profile. Do not claim human test results; none have been reported yet.

## Pending work after manual use ends

1. Run normal-user makepkg against the exact prepared public source via local source cache, preserving SHA checks; build dependencies use the existing Arch recipe.
2. Record the clone's installed package baseline/cache artifact before modifying it. Install/test in a clean synthetic profile; upgrade the v1.0 package (0.1.0) while retaining actual seeded words/cards/settings; remove while retaining data; restore baseline package/profile.
3. Run the relevant Linux full suite on final code. Host results remain reusable if product/tests do not change. Collect all failures in one batch before fixes.
4. Persist package/build/install/upgrade/removal hashes and cleanup evidence, then verify PUB-02, complete Phase 15 and finish the internal milestone. Publication remains outside scope.

Only identity-guarded clone UUID cf207909-94b5-4b49-8bd8-ccff973c1dc8 / SSH2227 is authorized. Do not control original arch-kde / SSH2223. Preserve user OCR/OMX edits. No native package installation/removal for Phase 15 has happened yet.
