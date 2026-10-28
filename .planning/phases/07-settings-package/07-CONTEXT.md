# Phase 7: Настройки, автозапуск и пакет — Context

**Gathered:** 2026-10-27
**Status:** Ready for research and planning
**Mode:** Agent-selected under explicit `gsd next --auto`; no human acceptance claimed.

<domain>
## Phase Boundary
SET-01, TRIG-04, INST-01, INST-02: native settings with actual runtime application, autostart, installable Arch PKGBUILD, Russian README and useful `lookup --doctor`. Preserve accepted lookup/learning behavior. Full game, sustained-load and performance acceptance remains Phase 8.
</domain>

<decisions>
## Implementation Decisions
- **D-01:** Enable the existing Settings tray action and reuse one native Qt/Breeze settings window. Expose global shortcut, dictionary enabled/order controls, popup timeout, online mode and autostart. System font/palette, keyboard access and fixed readable error/status copy follow current windows; no web frontend.
- **D-02:** Extend the existing per-field validated config compatibly; atomic writes retain unrelated valid settings and existing clients/dictionary identifiers. A bad individual value falls back without resetting other fields. No new dependency or alternate config framework. Use sensible bounded timeout controls, retaining the current 20-second default.
- **D-03:** Saved settings must affect the running app: next lookup uses the new dictionary set/order and online flag, next popup uses the chosen timeout, and the new physical global key triggers. Keep UI responsive during pending requests. Reload resources on their owning worker, preserve monotonically distinct accepted identities and refuse late pre-reload results; do not share SQLite or reuse generations after replacing an engine.
- **D-04:** Default shortcut remains Meta+Shift+D. Own only LookUpLinux registration/files; detect conflicts and report them instead of stealing unrelated shortcuts. A changed shortcut must actually replace the active old binding, not merely rewrite JSON/default desktop text. Preserve KDE external overrides where applicable and provide manual setup instructions. Never change KWin focus/security policy.
- **D-05:** Autostart defaults enabled to satisfy launch-on-login; the checkbox disables/enables it persistently. Use supported XDG/KDE autostart mechanisms and owned desktop entries. Registration paths/Exec quoting must work both from a source checkout and the installed package. Preserve unrelated files and user data.
- **D-06:** `makepkg -si` must install the application, required official-repository dependencies, Mueller 7 data, launchers and working shortcut registration. Resolve the known kdotool-AUR problem inside a reproducible package path: no undocumented manual AUR prerequisite. Research a pinned official helper source/build or release asset with verified provenance/checksum/license. Third-party licenses/attribution must accompany bundled data/helper; do not invent or change the project's own license.
- **D-07:** Pacman removal must remove package files, owned launchers and active shortcut registration without deleting history/cards/config or unrelated user entries. Research a safe lifecycle mechanism rather than privileged broad home-directory cleanup. Retained inert user preferences must be distinguished from a still-active registration.
- **D-08:** `lookup --doctor` explains missing packages/tools, unavailable or damaged dictionaries, kdotool/session capability and shortcut state using actionable Russian output and meaningful exit status. It must not trigger lookup, alter counts, read clipboard/screenshots or leak private query/history data. Online-disabled settings must not cause diagnostic network requests.
- **D-09:** README is Russian, written for a fresh reader: supported Arch/KDE Wayland, build/install/run/uninstall, dictionary paths/order, manual shortcut setup in current KDE shortcuts UI, autostart/settings, doctor and real known limits. Keep Anki/backend/context-provider limits accurate; do not imply sync or unsupported environments.
- **D-10:** Acceptance includes core config/lifecycle/doctor tests, real native settings changes with new-key/disabled-source/no-network/timeout checks, actual autostart after login and actual makepkg install/remove in the VM. Use an isolated clone/snapshot/profile when session or package operations would disturb existing work; do not roll back the user's active VM destructively. Isolate XDG settings/cache/data before Qt, use owned service names and restore test shortcut state. Record agent evidence honestly; no routine approval checkpoint under --auto.
- **Agent discretion:** Choose the smallest complete lifecycle/package implementation based on current source and primary documentation. Preserve existing CLI/import behavior and delayed lookup/card snapshot guarantees. No speculative framework or provider/model changes.
</decisions>

<canonical_refs>
## Canonical References
- `.planning/ROADMAP.md` — Phase 7 success criteria.
- `.planning/REQUIREMENTS.md` — SET-01, TRIG-04, INST-01, INST-02.
- `.planning/PROJECT.md` — accepted scope, original stack and decisions.
- `docs/lookupper/architecture.md`, `docs/lookupper/linux-requirements.md`, `docs/lookupper/evidence.md` — original observations versus Linux contracts.
- `.planning/phases/06-words-cards/06-02-SUMMARY.md` — current native owner, GUI connection and event snapshot contract.
- `.planning/phases/06-words-cards/06-03-SUMMARY.md` — actual native/Anki acceptance and the earlier Qt settings side effect; final test profiles isolate all XDG paths.
- `.planning/phases/05-app/05-VERIFICATION.md` — accepted shortcut/capture/focus behavior.
- `.planning/phases/04-vm/04-VERIFICATION.md` — KDE/VM capability evidence.
</canonical_refs>

<code_context>
## Existing Code Insights
- `lookup/config.py`: frozen Config currently dictionaries/online/clients, per-key tolerant loading, explicit LOOKUP_CONFIG and XDG paths; no writer yet.
- `lookup/app.py`: one long-lived worker resource context and monotonic generations; live config/dictionary reload is not yet implemented.
- `lookup/gui.py`: Settings placeholder, current 20s popup timeout, source desktop builder and owned native windows. Engine replacement must not allow queued old events to reuse identities.
- `lookup/platform.py`, `lookup/capture.py`: actual kdotool and capture paths/dependencies to inspect before packaging.
- `lookup/dicts.py`: user dictionary discovery must be reconciled with installed system Mueller data.
- `lookup/__main__.py`: existing mutually exclusive CLI actions; add doctor without importing GUI on core-only paths.
- `tools/check_app.py`, `tools/check_learning_app.py`: controlled native fixtures, actual shortcut checks, safe owned profiles and cleanup contracts.
</code_context>

<deferred>
## Deferred Ideas
Real games, long-run stability, clean-snapshot end-to-end installation and latency distribution remain Phase 8. No new languages, local models, audio, sync or other v2 scope.
</deferred>
