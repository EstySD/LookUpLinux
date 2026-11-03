# Local source snapshot: generate a ready build directory with tools/stage_package.py.
pkgname=lookup-linux
pkgver=0.2.1
pkgrel=1
pkgdesc='English-Russian cursor dictionary and learning cards for KDE Wayland (local build)'
arch=('x86_64')
options=('!strip' '!debug') # Pinned upstream helper is already stripped.
license=('GPL-3.0-or-later' 'Apache-2.0' 'LicenseRef-Mueller7-GPL-unspecified')
depends=('python' 'python-pyqt6' 'qt6-wayland' 'tesseract' 'tesseract-data-eng'
         'wl-clipboard>=2.3.0' 'libkscreen' 'kglobalacceld' 'kservice' 'dbus' 'glibc' 'gcc-libs' 'kwin>=6.8')
makedepends=('cmake' 'extra-cmake-modules' 'vulkan-headers')
source=('lookup-source.tar.gz'
        'kdotool-0.3.0.tar.gz::https://github.com/jinliu/kdotool/releases/download/v0.3.0/kdotool-0.3.0-x86_64-unknown-linux-gnu.tar.gz'
        'mueller7.tar.bz2::https://qstardict.ylsoftware.com/files/mueller7.tar.bz2')
sha256sums=('@LOCAL_SOURCE_SHA256@'
            '2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff'
            '1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed')

build() {
  cmake -S lookup-source/native/kwin-capture -B native-build -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
  cmake --build native-build
}

package() {
  DESTDIR="$pkgdir" cmake --install native-build
  install -d "$pkgdir/usr/lib/lookup/app" "$pkgdir/usr/share/lookup/dicts/mueller7"
  cp -r lookup-source/lookup "$pkgdir/usr/lib/lookup/app/"
  install -Dm755 lookup-source/packaging/lookup "$pkgdir/usr/bin/lookup"
  install -Dm755 kdotool "$pkgdir/usr/lib/lookup/kdotool"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/kdotool-APACHE-2.0"
  install -Dm644 lookup-source/packaging/THIRD-PARTY.md "$pkgdir/usr/share/licenses/$pkgname/THIRD-PARTY.md"
  install -Dm644 lookup-source/LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 lookup-source/COPYING.md "$pkgdir/usr/share/licenses/$pkgname/COPYING.md"
  for suffix in ifo idx.gz dict.dz; do
    install -m644 "mueller7/mueller7.$suffix" "$pkgdir/usr/share/lookup/dicts/mueller7/"
  done
  install -Dm644 lookup-source/packaging/org.lookup.Linux.desktop "$pkgdir/usr/share/applications/org.lookup.Linux.desktop"
  install -Dm644 lookup-source/packaging/org.lookup.Linux.Home.desktop "$pkgdir/usr/share/applications/org.lookup.Linux.Home.desktop"
  install -Dm644 lookup-source/packaging/org.lookup.Linux.autostart.desktop "$pkgdir/etc/xdg/autostart/org.lookup.Linux.desktop"
}
