# Validation workflow

Denis's persistent preference, recorded 2026-11-03:

- Run the complete relevant check set as one background batch. Parallelize independent checks; put dependent VM/GUI steps in a script.
- Wait for completion notification instead of repeatedly waking the model to inspect individual checks. Do not create an agent per test.
- Collect all failures first, fix them together, then rerun the affected checks as a batch. Repeat the full suite only after relevant changes or at the final required gate.
- Keep logs on disk and report a compact summary with failure excerpts. Avoid repetitive status messages and analysis while checks run.
- Save commands, job handles, report paths and tested source hashes so another session can reuse valid results.
- Apply this policy to GSD/auto workflows too. Preserve real acceptance gates, safe cleanup, user changes and honest agent-versus-human verification.


## Shared virtual machines (Denis, 2026-11-13)

Read `D:/vm/README.md` before Linux/Android work. Reuse VirtualBox `arch-kde`
(SSH `archvm`) and Android AVD `Pixel7a_A16` (Android 16, serial `emulator-5554`).
Do not create new VMs, clones, AVDs, isolated AVD homes or system images without
an explicit user instruction. Coordinate sequential use; never reset, stop or
reconfigure a shared device used by another task. Ubuntu/Android 14/TV coverage
is unavailable, not passed. This supersedes older project-specific VM advice.
