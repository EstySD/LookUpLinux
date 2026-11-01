#!/usr/bin/env bash
# Run inside the disposable Arch container, in a staged public build directory.
set -euo pipefail
pacman -Syu --noconfirm python sudo
useradd -m builder
echo 'builder ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/builder
chown -R builder:builder "$PWD"
sudo -u builder makepkg -s --noconfirm
packages=(lookup-linux-*.pkg.tar.zst)
test "${#packages[@]}" -eq 1
pacman -Qip "${packages[0]}"
if tar -tf "${packages[0]}" | grep -qi mueller; then
  echo 'Public package unexpectedly contains Mueller data' >&2
  exit 1
fi
pacman -U --noconfirm "${packages[0]}"
lookup --help
test -f /usr/share/licenses/lookup-linux/LICENSE
test -f /usr/share/licenses/lookup-linux/NOTICE-wordnet.txt
