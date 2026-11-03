# Releasing LookUp Linux

The release workflow builds **Arch Linux x86_64** assets and creates a **draft**.
It does not claim Windows/macOS support or automatically publish releases.

## Prepare

1. Keep versions aligned in both package recipes, the changelog, release notes,
   CI preview command. Current version: `0.2.1`.
2. Run tests with PyQt6 installed and `QT_QPA_PLATFORM=offscreen`.
3. Run `python tools/build_release.py --tag v0.2.1 --output dist` in a clean
   checkout. The output directory must be empty. Assets use explicit source
   roots; agent logs, planning, research and personal dictionaries are excluded.
   `.gitattributes` also excludes workspace artifacts from GitHub's automatic
   source archives. This does not erase files already present in Git history.
4. Review the source archive, licenses and checksums. Public staging uses
   `packaging/PKGBUILD.public` and never bundles Mueller. Do not substitute the
   root local-build recipe when creating public binaries.

## Build and review

After authorization to publish, push the reviewed release changes and
matching tag (`git tag -a v0.2.1 -m "LookUp Linux 0.2.1"`, then
`git push origin v0.2.1`). This triggers **Prepare release**. Manual dispatch
also accepts an existing release tag. An existing release is never overwritten;
resolve a failed rerun explicitly after inspecting the original draft.

The workflow tests the tagged source, creates source/build-kit archives, builds
a native package inside an Arch container as an ordinary user, generates
`SHA256SUMS`, uploads CI artifacts and creates the draft with platform-specific
download instructions. Arch uses rolling repositories; source archives are
deterministic, but byte-for-byte reproducible native builds are not promised.

Before publishing, test the downloaded package in a clean Arch x86_64 KDE
Plasma 6 Wayland session: install, tray startup, dictionary addition, selected
text lookup, cursor OCR, shortcut, settings, save/review/export, restart and
uninstall preserving personal data. Run `lookup --doctor`. Record environment,
results and remaining limits in the release notes. Label agent checks as agent
checks; never call them human acceptance. Then publish the reviewed draft.

## Repository discoverability

Suggested About description: **English–Russian OCR cursor dictionary and vocabulary
cards for KDE Plasma Wayland on Arch Linux. Offline StarDict/DSL/MDX + Anki export.**

Topics: `linux`, `arch-linux`, `kde`, `kde-plasma`, `wayland`, `ocr`, `dictionary`,
`translation`, `english-russian`, `vocabulary`, `spaced-repetition`, `anki`,
`python`, `pyqt6`, `stardict`.

Use the README banner for the repository identity. A real desktop screenshot
or short recording should be added only after capturing the application with
non-private sample text; the banner is an illustration, not a screenshot.
Enable private vulnerability reporting under repository Security settings.
Announcements to other communities are a separate maintainer action.

## AUR preparation

Follow [AUR.md](AUR.md) to prepare a recipe from the exact public source archive,
generate `.SRCINFO` with makepkg, and validate a local build before publication.
The public package requires separately supplied dictionaries and excludes Mueller.
