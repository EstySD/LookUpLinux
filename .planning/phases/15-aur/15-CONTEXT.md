# Phase 15: distribution preparation

Agent decisions under explicit --auto, single discussion pass:

- Version: prepare patch 0.2.1 because public v0.2.0 already exists. Internal milestone v1.1 does not change the external versioning scheme.
- Public package: use the existing public recipe, exclude Mueller, retain project/helper/WordNet notices, and keep the private/local recipe separate.
- AUR: produce a PKGBUILD with a fixed versioned public source URL and SHA256, plus actual makepkg-generated .SRCINFO. Build against the exact staged release source locally before publication. Do not publish a release or send to AUR in this task.
- Acceptance: build as a normal user in the identity-guarded owned clone, install in a clean synthetic profile, upgrade the v1.0 package (0.1.0) while retaining words/cards/settings, and uninstall without removing user data. Preserve the clone's original installed package/configuration afterwards.
- Batch policy: host regressions, release/archive checks and deterministic target build/lifecycle operations form one batch. Keep logs/source hashes on disk; fix collected failures together.
- Scope: current Arch/KDE package. No new Ubuntu port, new installer, new dependencies or product behavior unless necessary to repair a demonstrated packaging issue.

Publication is recorded as pending, independent from PUB-02 package readiness.

User clarification: prepare the new version only; no publication, push or AUR submission. User subsequently requested visible GUI VM/manual testing. The latest source preview is running in the owned clone; leave it running and do not perform package install/remove, restart the session or inject automated GUI input while Denis tests. Host checks and metadata preparation can continue independently. Target lifecycle acceptance remains pending until that manual-use constraint ends.
