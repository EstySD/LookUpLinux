# Phase 7: Settings, autostart and packaging — Research

**Researched:** 2026-10-28. **Confidence:** HIGH for inspected code/primary sources and recorded downloads; live replacement/uninstall/login still need execution evidence.

## User Constraints (from CONTEXT.md)


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


## Project Constraints and Requirements

[VERIFIED: supplied AGENTS.md] Work autonomously under --auto, preserve other changes, use scoped apply_patch edits, report agent evidence honestly. SET-01 covers effective settings; TRIG-04 actual login; INST-01 package/install/remove; INST-02 Russian docs/readonly diagnostics. Do not roll back the active VM. Isolate XDG_CONFIG_HOME, XDG_CACHE_HOME and XDG_DATA_HOME **before Qt creation**; previous QtProject.conf baseline was unknown. [VERIFIED: Phase6 summary and Phase7 context]

## Implementation-ready decisions

### Settings/config and worker ownership

[VERIFIED: lookup/config.py] Frozen Config currently has dictionaries/online/clients; per-key tolerant load already exists, no writer. Add shortcut, popup timeout (20-second default), autostart=true. Atomic writer reads bounded existing JSON, validates changed keys, preserves unrelated settings/clients/dictionary IDs, writes same-directory private temporary file then os.replace. Reject invalid edited values rather than silently saving defaults. A damaged one key must not reset valid others. Do not add a config framework.

[VERIFIED: lookup/app.py Engine._run/_resources] One worker owns long-lived DictSet/SQLite; replacing Engine would reset _generation and allow queued stale events to collide. Keep this Engine. Add condition-protected reload-pending flag and generation invalidation; consume reload on its worker between jobs, close/reopen dictionaries there, keep accepted identities monotonic. A pending old job may finish but current(id) must refuse its UI/history enrichment. Reload acknowledges success/failure asynchronously; never share connection/DictSet with GUI. Online=false prevents *next* network requests; already-started bounded network threads may finish but cannot publish stale values. Do not promise instantaneous network cancellation.

[VERIFIED: lookup/gui.py Owner/Popup] Enable/reuse one Settings window. Apply timeout to next popup timer; dictionaries need discovered IDs plus configured order/enabled flags. Preserve unknown configured IDs even if files temporarily unavailable. Saving/applying errors remain visible; do not claim successful runtime application until acknowledged. Keep learning snapshots independent.

### Actual KDE shortcut change

[VERIFIED: live VM introspection before shutdown; CITED: KDE org.kde.KGlobalAccel.xml and kglobalacceld.cpp] Session service org.kde.kglobalaccel, path /kglobalaccel, interface org.kde.KGlobalAccel exposes shortcut(as)->ai, isGlobalShortcutAvailable(i,s)->b, setForeignShortcut(as,ai), unregister(s,s)->b and newer sequence APIs. Use a **single-chord** QKeySequence, portable text and key[0].toCombined() (validate nonzero, no multi-chord). Restrict action identity to [org.lookup.Linux.desktop, _launch, LookUp Linux, LookUp Linux]; retrieve actual registered identity if friendly text differs.

[CITED: KDE kglobalacceld.cpp] setForeignShortcut dispatches to setForeignShortcutKeys with NoAutoloading, which replaces keys and emits change signal. For this verified VM API, it avoids difficult a(ai) PyQt marshalling. These legacy methods exist on target but are deprecated upstream; keep calls behind one small adapter. Do not assume changing X-KDE-Shortcuts changes an existing active binding.

Preflight availability excluding own component; never steal. Snapshot actual current keys, set only owned action, read back and require exact match. Restore previous binding if save/apply fails. On initial registration preserve external KDE overrides: use actual current key when present; only explicit Settings key edits overwrite it. If desired key conflicts, leave old binding/config intact and report conflict. Verify old physical key stops and new key triggers in native execution. [VERIFIED: target introspection; CITED: KDE source semantics; selected safety design]

[VERIFIED: lookup/gui.py desktop_text] Existing desktop builder writes absolute Python -m lookup --trigger plus checkout Path and default key. Installed desktop must instead use installed absolute /usr/bin/lookup --trigger without checkout Path. Use package-owned /usr/share/applications/org.lookup.Linux.desktop for trigger, optional separate launcher/action for words. Never create an unnecessary user copy shadowing the package. Source mode may create one explicitly owned marked entry with safe quoting.

### Autostart and removal

[CITED: freedesktop Autostart specification] System /etc/xdg/autostart entry is supported, user entry takes precedence, TryExec must resolve. Install one package-owned entry with OnlyShowIn=KDE;, TryExec=/usr/bin/lookup, Exec=/usr/bin/lookup --autostart. **Selected design:** --autostart reads own JSON flag before Qt and exits when disabled. Checkbox only writes own JSON, avoiding root/system desktop writes. Source mode uses owned user autostart entry with absolute executable/check-out path. File execution alone does not prove actual login; test a real separate login.

[CITED: KDE globalshortcutsregistry.cpp refreshServices] KSycoca service refresh removes components whose desktop file no longer exists, then discovers new applications. Thus removing package desktop can deactivate its shortcut without deleting user home preferences. First test this actual automatic path after pacman removal; a cached inert preference is not active registration. If explicit hook cleanup is needed, restrict to owned component/_launch on active user session buses with finite timeout, never arbitrary shell expansion, home scanning/deletion, unrelated shortcuts or user data. This fallback is not yet live-verified. Package uninstall must remove installed files/autostart and active shortcut, preserve DB/cards/config and unrelated entries. Preserve/identify source-mode user overrides rather than removing unmarked files. [VERIFIED: scope; source read]

### Reproducible package

[VERIFIED: source-probes.json downloaded upstream bytes] Prefer pinned **official x86_64 release helper** in a private /usr/lib/lookup/kdotool path, avoiding both AUR and conflict with user's /usr/local/bin helper. Route production platform helper calls to packaged path when installed, retain PATH fallback for source mode. No Rust build dependency needed. Upstream release API digest and independently downloaded SHA256 agree:

- https://github.com/jinliu/kdotool/releases/download/v0.3.0/kdotool-0.3.0-x86_64-unknown-linux-gnu.tar.gz
  SHA256: 2079cc1d492b6e83e04def4d9376e34fcb36a4e3bdc637c8c2ee6fa547ce90ff
- https://qstardict.ylsoftware.com/files/mueller7.tar.bz2
  SHA256: 1c5e19b857eaa5fc98f77173e8baeb22cb654c407586465b4270e4286bf070ed
- Optional source provenance: https://codeload.github.com/jinliu/kdotool/tar.gz/refs/tags/v0.3.0
  SHA256: 78e969941b1861aad849cad9bff7c34d34268912bf8042d5b3e9fbebcbb96f6d

[VERIFIED: archive metadata] Helper is Apache-2.0, release includes LICENSE. Mueller archive has .ifo/.idx.gz/.dict.dz plus redundant plain .dict and stray swap; package only required three dictionary files under /usr/share/lookup/dicts/mueller7/. QStarDict labels GPL; archive itself carries **no license text/version**. Preserve attributed upstream GPL notice and evidence; obtain correct GPL text/precise version from verified distribution source before declaring GPL-2.0-or-later. Do not silently invent it. Project has no tracked LICENSE/COPYING, so do not assign a new project license; describe it as unspecified/custom metadata for local packaging. Public redistribution license resolution remains separate.

[VERIFIED: lookup/dicts.py] SYSTEM_DICT_ROOT already /usr/share/lookup/dicts. Install Python package in version-appropriate site-packages or /usr/lib/lookup with a self-contained absolute wrapper; include lookup/data resources. Avoid pip/network package() actions. Package source snapshot must be deterministic/pinned or clearly local staged source; do not package .planning/tests/user data. Pin all downloaded sources/checksums; do not use SKIP for third-party assets.

[VERIFIED: earlier VM pacman probe] Official packages present: python3.14.8, python-pyqt6, tesseract, tesseract-data-eng, wl-clipboard>=2.3, libkscreen, kglobalacceld, kservice, qt6-tools, desktop-file-utils; base-devel/makepkg available. Select actual runtime dependencies from these (plus dbus/glibc helper runtime), use ldd on bundled helper during execution. Source checkout installed helper is /usr/local/bin/kdotool. Screenshot2 is production capture; Spectacle optional fallback only if retained. Verify installed ScreenShot2 authorization rather than changing KWin security policy. [VERIFIED: capture.py and Phase4 evidence]

### Doctor and README

[VERIFIED: CLI lazy import convention] Add mutually exclusive --doctor with fixed Russian diagnostics and meaningful exit status. Read config, discover/open dictionary metadata with bounded time, check command versions/session bus availability and owned shortcut/desktop state. Never start lookup, read PRIMARY, capture image, increment history or perform network probes. Missing session should be actionable, not crash; distinguish disabled dict from corrupt/missing. Do not emit personal paths/content unnecessarily. Russian README must explain clean installation, source/installed paths, current KDE shortcut UI/manual alternative, defaults, configuration/autostart, uninstall/user-data retention and known provider429/Anki limits. No sync/unsupported-DE promises.

## Environment Availability and validation

[VERIFIED: read-only host and earlier VM probes] arch-kde currently **powered off**, no snapshots. Main VDI at D:/vm/machines/arch-kde/arch-kde.vdi, host D free ~228GB; earlier guest / free31GB. Existing account arch UID1000, sudo -n succeeds; makepkg/base-devel available, cargo absent. Full owned clone while powered off is viable; do not start/log out/revert main VM in research. Execution must avoid duplicate NAT forwarding port2223/MAC and use separate VM name/disk/profile. Do not claim clone created or login/package checks performed.

### Validation Architecture

[VERIFIED: project tests] stdlib unittest focused config/settings/lifecycle/doctor/package tests, then full VM discovery. Required cases:
- per-key bad values, preserved clients/IDs/unknown keys, atomic failure/no truncation/private permissions;
- worker reload during delayed job, monotonic IDs, no stale UI/history, next dictionary order/online behavior, retained card snapshots;
- shortcut collision/refusal/rollback/actual readback, external override preservation; physical old/new key;
- settings native checkbox/order/timeout and keyboard/empty/error states, no network when disabled;
- doctor read-only spies: no clipboard/capture/network/history change, missing tools/session/corrupt dictionary and useful exit codes;
- makepkg source checksums + desktop-file-validate; actual makepkg -si, installed imports/resources/helper/Mueller/physical shortcut, actual login autostart true/false, pacman -R removes files/active binding and preserves user data/unrelated entries;
- collect isolated XDG baseline **before Qt**, restore owned service/files/key releases, assert cleanup. All acceptance agent-run; clean-snapshot overall reliability remains Phase8.

## Sources / uncertainties

[CITED] https://raw.githubusercontent.com/KDE/kglobalaccel/master/src/org.kde.KGlobalAccel.xml ; https://raw.githubusercontent.com/KDE/kglobalacceld/master/src/kglobalacceld.cpp ; https://raw.githubusercontent.com/KDE/kglobalacceld/master/src/globalshortcutsregistry.cpp ; https://api.kde.org/kglobalaccel.html ; https://specifications.freedesktop.org/autostart/latest/ ; https://man.archlinux.org/man/PKGBUILD.5.en ; https://qstardict.ylsoftware.com/dictionaries.php ; https://github.com/jinliu/kdotool/releases/tag/v0.3.0 .

[VERIFIED: probe_sources.py/source-probes.json] Release/dictionary downloads and hashes are preserved, not invented. Live changing binding/automatic package-removal cleanup/login/installed capture remain **execution verification gates**, not research passes. Mueller exact license version is unresolved in the archive; project license remains unspecified. No technical blocker to local implementation, but do not claim redistribution licensing settled.
