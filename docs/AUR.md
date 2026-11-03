# Preparing the Arch/AUR package

Version 0.2.1 is prepared locally and **not published**. The AUR source URL is a
future release-asset URL; its presence in a PKGBUILD does not make it available.
Publishing a GitHub release or submitting an AUR package requires a separate
maintainer action after authorization.

## Prepare exact source and recipe

From the repository root, use new or empty output directories:

```sh
python tools/build_release.py --tag v0.2.1 --output dist
python tools/stage_aur.py --source dist/lookup-linux-0.2.1-source.tar.gz --output aur-build
cp dist/lookup-linux-0.2.1-source.tar.gz aur-build/
cd aur-build
makepkg --printsrcinfo > .SRCINFO
makepkg --verifysource
makepkg -s
```

Build as an ordinary user on Arch Linux x86_64 with KDE Plasma 6.8 or newer.
`makepkg -s` installs declared build/runtime dependencies through pacman.
During preparation, the copied source archive satisfies the future URL from
makepkg's local source cache; all SHA256 checks remain enabled. The helper
archive is downloaded from its pinned upstream URL and checksum.

The public recipe comes from `packaging/PKGBUILD.public`. It includes the native
KWin plugin and private kdotool helper, and retains project, helper and WordNet
license notices. It does not bundle Mueller or personal dictionaries. Add a
dictionary using [DICTIONARIES.md](DICTIONARIES.md).

## Install, upgrade and remove

```sh
sudo pacman -U ./lookup-linux-0.2.1-1-x86_64.pkg.tar.zst
lookup --app
lookup --doctor
```

Quit the running application before upgrading so loaded Python code and the
history connection are reopened. Upgrade using `pacman -U` with the new package.
Package scripts do not remove user history, cards, dictionaries or settings.
Keep a backup of those files before an actual workstation upgrade.

For removal, quit LookUp and run `sudo pacman -R lookup-linux`. Personal data
under the user's configuration/data directories remains. Removal does not stop
an already loaded process; do not use package removal as a process-control tool.

## Maintainer handoff

Retain `SHA256SUMS`, the public source archive, generated `PKGBUILD`, `.SRCINFO`,
`AUR.json` and the package validation report. Regenerate the source and recipe
after any source change, and regenerate `.SRCINFO` from the final PKGBUILD.
Never copy `.SRCINFO` forward by hand or replace source checksums with `SKIP`.

After publication is separately authorized, verify that the released source
bytes match the prepared SHA256 before submitting metadata to AUR. Until then,
all publication status remains pending. See the official
[PKGBUILD manual](https://man.archlinux.org/man/PKGBUILD.5.en) and
[source metadata manual](https://man.archlinux.org/man/SRCINFO.5.en).
