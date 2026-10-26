# Phase5 — Pattern Map

| Responsibility | Actual source / application |
|---|---|
| Main result + slow context | translate.lookup: optional detached on_ready before existing finite context join; default CLI untouched |
| History finalization | store.upsert_word: one normalized-key autocommit event under current-generation guard |
| Cache ownership | translate.lookup(save=False) STILL writes translations/meta; serial worker connection owns all SQL |
| Typed UI data | translate.Result snapshots + immutable dicts.Article; separate save_error envelope |
| Capture pipeline | platform.cursor_position/monitors/monitor_at/image_point + capture.capture_monitor + ocr.recognize_image/choose_query |
| Primary | platform.read_primary with in-memory consumed identity; new/unchanged/empty transitions explicit |
| Geometry/focus | platform.popup_rect,owned_window,window_action; current UUID/PID checks |
| Owner/client | tools/vm_spike.py is behavioral reference ONLY; production lazy module owns fixed QtDBus Trigger; no tool import |
| GUI lifecycle | Native QWidget scroll surface,QSystemTrayIcon/QMenu,finite QTimer; retained objects; disabled future actions |
| Tests | _support isolated paths/network guards; Events/barriers for races; actual worker-created SQLite |

Suggested production files: lookup/app.py(stdlib engine/controller),
lookup/gui.py(lazy Qt owner/popup/tray). Planner may choose equivalent compact
names. Avoid a framework/event-bus hierarchy. Preserve lookup --word/--image
and python -S core imports. Source inspection:2026-10-26.
