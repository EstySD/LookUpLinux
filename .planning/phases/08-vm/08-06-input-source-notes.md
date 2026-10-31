# AssaultCube physical mouse settling investigation

Read-only investigation on 2026-10-31; no VM mutation or game/source patch.

Source: https://raw.githubusercontent.com/assaultcube/AC/v1.3.0.2/source/src/main.cpp
Actual fetched SHA256: 4766346cb1fced10e784b7baaf8581c48a3383ffecfee996a23a2eeffb224f3a (1608 lines; web extraction may use different line offsets).

- Lines 841/960: startup counter discards five mouse-motion events; its only occurrences in this file are initialization and decrement. Focus handling does not reset it here.
- Lines 944-969: focus gain schedules grab; an ungrabbed mouse event can acquire it without contributing camera displacement. Queued motion may coalesce.
- Lines 1018-1023: accumulated nonzero displacement reaches camera movement. Supported event debugging can expose received SDL motion, but has not been enabled or treated as proof.
- Physics source, `mousemove`: paused/intermission/follow spectator states suppress turning. Console source, `keypress`: open command entry consumes movement keys.

Bounded next native recipe: close console/menus; verify actual active game and lock; send eight small alternating physical horizontal pulses (+4/-4), 150 ms apart, then verify fresh grab and source frame. After lookup dismissal, record separate W movement, settle the physical mouse the same way, then measure the existing two +60 camera pulses with fresh independent frames. Settling is not accepted control proof. Keep the unchanged world ROI threshold and reject zero world change. This is a source-supported hypothesis, not proof of why a particular earlier attempt failed; capture actual SDL motion if physical settling still fails.

Original-running takeover currently blocks boot. Retained accepted-route1 camera changes zero world pixels and remains unaccepted.
