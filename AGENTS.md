# Validation workflow

Denis's persistent preference, recorded 2026-11-03:

- Run the complete relevant check set as one background batch. Parallelize independent checks; put dependent VM/GUI steps in a script.
- Wait for completion notification instead of repeatedly waking the model to inspect individual checks. Do not create an agent per test.
- Collect all failures first, fix them together, then rerun the affected checks as a batch. Repeat the full suite only after relevant changes or at the final required gate.
- Keep logs on disk and report a compact summary with failure excerpts. Avoid repetitive status messages and analysis while checks run.
- Save commands, job handles, report paths and tested source hashes so another session can reuse valid results.
- Apply this policy to GSD/auto workflows too. Preserve real acceptance gates, safe cleanup, user changes and honest agent-versus-human verification.
