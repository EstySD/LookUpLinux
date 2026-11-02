# Phase 9 capture boundary review

Scope: native/kwin-capture/capture.cpp and lookup/capture.py. Agent review,
2026-11-02. Native plugin is administrator-installed code inside the user's
compositor; same-UID ownership of org.lookup.Linux is the existing application
IPC trust boundary. No web or network endpoint was added.

## Findings

- Functional fail-closed gap (low, local resource exhaustion): Take's memfd
  allocation/write/seal failure paths returned an empty map. The consumer
  interprets that as a non-hotkey request and falls back to a live screenshot,
  potentially selecting a later scene. Return an explicit capture_failed map
  on those paths. This finding is recorded before remediation.

## Boundaries checked

- Spoofing/disclosure: Take compares the D-Bus sender's unique name to the
  current owner of org.lookup.Linux before touching frame data. Other session
  peers cannot consume or clear the pending frame. Version exposes no pixels.
- Tampering: returned anonymous memory is sealed against writes/resizing;
  raw layout, dimensions, exact FD length, finite coordinates and event times
  are validated before constructing an image. No pickle, shell expansion or
  arbitrary path is accepted from the peer.
- Disclosure: only the configured existing shortcut produces a frame; repeats,
  unrelated keys and locked-screen input are ignored. Lock changes clear the
  buffer. One bounded frame expires after five seconds; an expired error marker
  contains no pixels. No frame is stored on disk or sent to a provider.
- Denial of service: capture is capped at 256 MiB/16384 pixels per dimension;
  only one frame is retained and consumed once. GPU driver stalls and KWin's
  private native ABI remain platform risks; the module must be rebuilt after
  KWin upgrades. The measured actual synchronous capture is checked separately.
- Privilege: code runs as the existing compositor user, adds no privileged
  service, changes no KWin permission policy and registers no competing shortcut.
- Privacy/repudiation: production telemetry is opt-in and numeric. No arbitrary
  keystrokes or recognized text are logged by the native module. Public test
  fixture text in the acceptance harness is separate from production telemetry.

No high/critical finding was identified in the reviewed boundary. GPU drivers,
KWin internals and other pre-existing application subsystems are outside this
review. Actual unauthorized-consumer, expiry and single-consumption probes are
required alongside the functional acceptance results.

## Remediation and current validation

The recorded memfd allocation/write/seal gap is fixed in 4623670: those paths
return capture_failed, and expiry returns an error instead of live recapture.
Empty consumed-frame markers prevent late duplicate desktop clients from
invalidating the current retained request and contain no pixels.

09-native-security.json records actual unrelated-peer rejection, authorized
first consumption, duplicate rejection and expiry rejection on final native
code. Boundary tests reject malformed layouts, short FD reads and expired
frames. Weak-reference tests prove raw pixels are not held during translation
or idle failed-resource states. Pointer history is capped at 128 in-memory
positions and logs no arbitrary keys. Compositor FD exhaustion was not injected;
those three fail-closed branches were reviewed statically. No high/critical
unresolved finding remains in this reviewed boundary.
