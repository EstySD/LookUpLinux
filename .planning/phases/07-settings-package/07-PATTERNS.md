# Phase 7: Settings, autostart and package — Pattern Map

**Mapped:** 2026-10-28. Scope inferred from 07-CONTEXT.md and 07-RESEARCH.md; filenames for new modules remain planner choices.

## File Classification

| New/modified file | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| lookup/config.py | config | file-I/O/transform | existing load/_parse_dictionaries; learning._export for atomic write | exact/partial |
| lookup/app.py | service | event-driven | existing Engine/_resources | exact |
| lookup/settings_gui.py (new) | component | event-driven | lookup/learning_gui.py components/WordsWindow | exact |
| lookup/gui.py | controller | event-driven | Owner._open_learning and Bridge | exact |
| lookup/shortcuts.py or lifecycle module (new) | service | request-response/file-I/O | platform.run; gui.desktop_text | partial |
| lookup/platform.py | utility | request-response | existing bounded run/helper callers | exact |
| lookup/doctor.py (new) | utility | request-response/batch | platform probes; __main__ fixed diagnostic maps | partial |
| lookup/__main__.py | controller | request-response | existing action group/lazy GUI dispatch | exact |
| lookup/dicts.py (only if needed) | provider | file-I/O/transform | existing dict_roots/discover/open_all | exact |
| PKGBUILD, installed wrapper/desktop/autostart entries, attribution | config | batch/file-I/O | gui.desktop_text; tools/lookup.desktop.in | partial; no package analog |
| README.md | documentation | static | docs/lookupper/README.md for reference index only | no installation-guide analog |
| tests/test_config.py, test_app.py, new settings/lifecycle/doctor/package tests | test | batch/event-driven | existing config/Engine tests; test_learning_gui.py and test_cli.py | exact/role |
| tools/check_settings_app.py and package/login acceptance (new) | test | event-driven/batch | tools/check_learning_app.py; tools/check_app.py | exact/role |

## Pattern Assignments

### Configuration validation and atomic persistence

**Analogs:** lookup/config.py:22–28, 53–72, 81–103; lookup/learning.py:185–216.

```python
@dataclass(frozen=True)
class Config:
    dictionaries: tuple[tuple[str, bool], ...] = ()
    online: bool = True
    clients: tuple[str, ...] | None = None
```

```python
enabled = entry.get("enabled", True)
if not isinstance(enabled, bool):
    continue
if ident in seen:
    continue
seen.add(ident)
out.append((ident, enabled))
```

Keep stdlib imports, frozen defaults and per-key validation; IDs are compared to discovery results, never joined as paths. config_path/cache_dir create nothing. Read at most MAX_CONFIG_BYTES+1. New writes must preserve unrelated existing keys and configured-but-missing IDs; validation of edited fields should fail visibly rather than silently accept defaults.

Atomic-write analog (learning._export): same-directory NamedTemporaryFile(delete=False), stream.flush(), os.fsync(stream.fileno()), os.replace(temporary,path), cleanup temporary in finally. Reuse this sequence locally without importing learning/export concerns into config. Add bounded JSON read and private config permissions.

### Worker reload and identity ownership

**Analog:** lookup/app.py:127–157 (_resources), 160–247 (Engine), 281–326 (ready/enrichment guard).

```python
with self._condition:
    if self._stopping:
        return None
    self._generation+=1
    self._started=time.perf_counter()
    self._pending=None
    return self._generation
```

```python
with self._resources() as resources:
    while True:
        with self._condition:
            self._condition.wait_for(lambda:self._stopping or self._pending is not None)
            if self._stopping:
                return
            identity,started=self._pending
            self._pending=None
        self._process(identity,started,resources)
```

Extend this worker/condition lifecycle to consume reload and reopen resources on that same thread. Never replace Engine and reset identities. current(id) guards GUI publication and history/enrichment; reload invalidates pending/old work before changing resources. Keep fixed private reason codes at the outer exception boundary. Reload acknowledgement needs its own observable revision/status so a superseded result cannot announce current settings applied.

### Native settings components and Owner integration

**Analog:** lookup/learning_gui.py:20–38, 40–87; lookup/gui.py:417–491.

```python
def components():
    global _components
    if _components is not None:
        return _components
    from PyQt6.QtCore import Qt,QDateTime,pyqtSignal
    from PyQt6.QtWidgets import (QWidget,QLabel,QVBoxLayout,QHBoxLayout,QLineEdit,
                                QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,
                                QHeaderView,QFileDialog,QTextEdit)
```

```python
value=QLabel(text)
value.setTextFormat(Qt.TextFormat.PlainText)
value.setWordWrap(True)
value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
if name:value.setAccessibleName(name)
```

Use lazy Qt factory, native palette/fonts/layout widgets, Russian copy, explicit signals and injectable data/services. Owner._open_learning imports the factory only on demand, stores one window, refreshes, shows/raises/activates it, and catches typed persistence exceptions to fixed UI text. Apply that ownership to settings, keeping source/config operations outside widget formatting. Bridge connects worker events with Qt.ConnectionType.QueuedConnection (gui.py:433–435); reuse that thread boundary for reload acknowledgement. Do not pass worker-owned SQLite/DictSet to settings. Enable existing future_actions[2], preserve its list shape for existing consumers.

### Bounded desktop/session operations and diagnostics

**Analogs:** lookup/platform.py:14–79; lookup/gui.py:62–79; lookup/__main__.py:140–170.

```python
class PlatformError(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)
```

```python
child = subprocess.Popen(argv, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, shell=False, bufsize=0,
                         start_new_session=os.name == 'posix',
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
```

platform.run bounds lifetime/output and cleans process groups; use finite timeouts, argument lists and fixed reason codes for doctor/helper probes. No shell interpolation. Keep module import stdlib-only. KDE shortcut D-Bus calls have no exact existing replacement analog: implement research's narrow owned action adapter with collision/readback/rollback, not an invented generic registration layer.

gui.desktop_text validates absolute paths and rejects CR/LF/NUL; escapes backslash, quotes, backtick, dollar and percent for Desktop Entry Exec. Retain tested source quoting; installed entries use installed executable without checkout Path. Do not copy source-mode user desktop creation into installed-mode startup.

CLI uses required mutually exclusive action group and only imports lookup.gui.run inside app/trigger dispatch. Add doctor/autostart actions at that dispatch boundary; doctor must not call lookup/store/clipboard/capture/network. Existing reason dictionaries provide fixed Russian messages, never raw exception/query contents.

### Regression and actual native acceptance

**Analogs:** tests/test_config.py:12–105; tests/test_app.py:20–90; tools/check_learning_app.py:20–34, 115–137, cleanup from line300.

```python
def env(self, **values):
    return mock.patch.dict(os.environ, values, clear=True)
```

```python
@contextlib.contextmanager
def resources(self):
    self.owners.append(('open',threading.get_ident()))
    # Yield worker-created resources; record close/find thread identities.
```

Tests use unittest, tests._support.make_tempdir(self), forbid_network(self), injected sources/resources/lookup, threading.Event barriers and bounded waits. Extend observable delayed-ready replacement tests for reload; assert exact accepted history/events and resource-owner identity, not implementation internals alone.

Native harness has explicit REQUIRED_GATES and REQUIRED_CLEANUP frozensets, accepts only all required true flags with no error, and writes honest JSON evidence. Isolate LOOKUP_* plus XDG_CONFIG_HOME/CACHE_HOME/DATA_HOME before importing/creating Qt; retain XDG_RUNTIME_DIR and DBUS_SESSION_BUS_ADDRESS. Clean worker/windows/database/profile in finally. New physical-key/login/package gates require real clone execution; a mocked or directly invoked trigger is insufficient evidence.

## Shared Patterns

- No top-level Qt dependency in core/config/platform/doctor/settings factory modules.
- Thread-owned resources and monotonically invalidated identities protect lookup/history/card snapshots.
- Plain text user-derived content; fixed private errors; no clipboard/image/history reads during diagnostics.
- Explicit ownership of desktop/service entries and temporary profiles; preserve unrelated files/settings.
- Dict discovery already includes /usr/share/lookup/dicts (dicts.py:263–309); package Mueller there instead of adding a second search convention.

## No Close Analog

PKGBUILD/install-removal/login lifecycle and actual shortcut replacement have no complete existing implementation. Use 07-RESEARCH.md primary sources, pin downloaded bytes, retain license uncertainty, and require real install/login/remove evidence. README needs a fresh-reader Russian installation guide; reverse-engineering docs are references, not a package contract.

## Metadata

Search scope: lookup/, tests/, tools/ and Phase7 context/research. Five primary analog families: config/atomic file I/O, Engine, native Owner/windows, bounded platform/CLI, tests/native harness. No source files changed.
