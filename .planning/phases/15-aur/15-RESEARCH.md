# Packaging evidence and approach

Existing tools/stage_package.py creates deterministic allowlisted source tarballs and substitutes the local SHA into the chosen package template. tools/build_release.py creates a public source archive and an Arch build kit. The public recipe has no bundled Mueller. v1.0's recipe installs 0.1.0, while current public version is 0.2.0; remote v0.2.0 and main exist, so use a new patch version.

Found gap: the standalone public source archive omits native/kwin-capture, although the build kit includes it. A source-based AUR build requires CMakeLists.txt, capture.cpp, metadata.json and README.md. Include only those text/native inputs and add a regression assertion.

Generate AUR metadata from packaging/PKGBUILD.public, changing its first source to the versioned source asset and its source-directory references to that asset's top-level directory. Keep the pinned helper checksum. Generate .SRCINFO using makepkg --printsrcinfo; never maintain it independently.

Primary references retrieved 2026-11-03: https://man.archlinux.org/man/PKGBUILD.5.en and https://man.archlinux.org/man/SRCINFO.5.en . Local receipts in host TEMP lookup-pkgbuild-man.html and lookup-srcinfo-man.html. Native makepkg is the final parser/metadata authority.

An unpublished source URL cannot be tested as a public download. Build the exact same archive through a local source cache and record the future URL as pending publication, rather than pretending it exists.
