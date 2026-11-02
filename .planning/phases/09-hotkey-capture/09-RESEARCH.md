# Phase 9: source findings

Date: 2026-11-02. Local source inspection; target baseline pending.

## Current capture path

`Controller.Trigger` timestamps entry, starts a generation, hides the popup and waits a fixed 75 ms before enqueueing. `Engine` initializes dictionaries/SQLite before processing pending work; an active prior lookup can delay the next capture. `Source.freeze` then samples cursor coordinates, queries monitor topology and work area, reads PRIMARY (bounded at 500 ms), and finally requests ScreenShot2. These intervening operations allow the cursor and source scene to change before the frame is available.

`Frozen` already retains an immutable coordinate tuple and Capture bytes; OCR uses those values rather than recapturing. This protects post-capture processing but does not prove capture at hotkey time. Moving capture earlier must account for QtDBus authorization, stale requests, previous popup hiding, PRIMARY precedence and resource ownership.

## Measurement and implementation order

1. Establish a current baseline on the owned KDE Wayland clone, with real input and synthetic changing text. Include cold/warm, transport and useful-result stages.
2. Freeze numerical capture/result budgets from baseline before changing runtime behavior.
3. Move request capture out of queued translation/resource work, remove only measured unnecessary waits and preserve current privacy and request identity semantics.
4. Repeat identical target scenarios and host regressions. Host mocks cannot satisfy CAPT-06/CAPT-07 or target latency acceptance.

## Risks

Cursor and frame come from separate compositor calls. Their temporal consistency requires a real moving-scene probe; do not describe it as atomic without evidence. A fixed timer removal alone cannot satisfy these requirements. The target VM was powered off at entry; boot only the pinned owned clone and retain restoration evidence.
