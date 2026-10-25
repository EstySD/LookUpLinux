# Phase 4 — Pattern Map

Read source: 2026-10-25. No implementation changed by research.

| Proposed responsibility | Reuse / analog | Constraint |
|---|---|---|
| Logical monitor → source pixels | lookup/ocr.py Transform and geometry tests | Pure stdlib function; subtract origin before ratio; actual dimensions |
| Capture image → OCR | lookup/ocr.py recognize_image / Recognition | Existing accepted defaults and quiet fixed errors; prefer memory input adapter if required |
| Fixed platform errors | OcrError / online.TranslateError | Enumerated reason, suppressed details; CLI/harness prints |
| Stage timing | lookup/__main__.py and OCR timings dict | Probe/capture/OCR durations; no private text or tokens |
| Fake subprocess/negative cases | tests/test_ocr_image.py | Assert argument list, timeout, no output/files, cleanup |
| Isolated paths | tests/_support.py make_tempdir | Never use real user DB/config paths in portable tests |
| Real VM harness | tools/calibrate_ocr.py / gen_ocr_fixtures.py | Independent expected public text and explicit provenance/results |
| Spike Qt host | New narrow tools/vm_spike.py (planner may rename) | Own unique service/window/desktop entry; no production app yet |

Platform adapter imports must keep ordinary core and word CLI functional on
Windows without Qt/Wayland. Separate pure geometry from QtDBus/GUI operations.
Do not make untested KWin/session assumptions: kdotool needs KDE_SESSION_VERSION
in SSH; target is presently locked; only one output exists.

Live ScreenShot2 probe discovered PyQt marshalling behavior: nonempty options
dict plus direct QDBusUnixFileDescriptor works; empty dict fails. Target6.8
returned InvalidScreen for intentional nonexistent output, so do not add old
interpreter-wide permission whitelisting.
