# Hotkey-time capture for KDE Wayland

The Python desktop trigger starts after the original key event. Sampling the
pointer or taking a screenshot at that later point can select a different word.
This small KWin plugin observes only the existing configured LookUp shortcut
and renders the pointed output synchronously in that input event, before KWin
processes subsequent pointer events or client surface commits. It does not
register another shortcut or consume input.

One bounded frame is held in compositor memory for at most five seconds. The
LookUp daemon consumes it once through a sealed anonymous memory FD. No frame
is written to a filesystem. Other bus callers cannot consume it. Locked-screen
events, auto repeats, other keys and invalid/unconfigured bindings are ignored.
LookUp windows are excluded from the snapshot so repeated lookup does not
recognize the previous popup.

Consumed frames leave a five-second numeric deduplication marker. Late desktop
activations for that frame are ignored before starting another request; they
must not recapture a newer scene. A new physical shortcut always replaces the
marker. Direct `--trigger` retries within that window are coalesced as well.

The normal PKGBUILD builds and installs this module. For a source checkout:

```sh
cmake -S native/kwin-capture -B build/kwin-capture -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build/kwin-capture
sudo cmake --install build/kwin-capture
python -m lookup --app
```

Build dependencies: the installed KWin 6.8+ SDK, CMake, extra-cmake-modules,
Vulkan headers and the SDK's Qt/KF6 dependencies. KWin's native plugin ABI
requires rebuilding this module after a KWin version upgrade. A mismatched
module is rejected by KWin; `lookup --doctor` reports availability. Source runs
without the module retain the ordinary capture backend, which cannot promise
capture at the physical key event.

The offscreen rendering sequence is adapted from KWin 6.8.1's screenshot
plugin, Copyright 2010 Martin Graesslin, 2021 Vlad Zahorodnii and 2025 Xaver
Hugl, GPL-2.0-or-later (used under GPL-3.0-or-later). See the project COPYING.md.
