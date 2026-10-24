"""config.json reader and config/cache directory resolvers (D-03, D-13, D-17).

The file is user-editable (and later written by the settings window), so every
key is validated on its own and damage degrades to defaults. Nothing here
creates files or directories, and nothing is printed or logged (V7).
"""
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

CONFIG_ENV = "LOOKUP_CONFIG"
CACHE_ENV = "LOOKUP_CACHE"
MAX_CONFIG_BYTES = 1 << 20
MAX_ID_CHARS = 512

# A client name ends up in a request URL (T-02-08): keep it boring.
_CLIENT_RE = re.compile(r"[A-Za-z0-9._-]{1,32}\Z")


@dataclass(frozen=True)
class Config:
    # (dictionary id, enabled) in the user's order; the id is only ever compared
    # with discovered dictionaries by the search layer, never joined to a path.
    dictionaries: tuple[tuple[str, bool], ...] = ()
    online: bool = True
    clients: tuple[str, ...] | None = None


def config_path() -> Path:
    """Resolve the config file path. Creates nothing on disk."""
    explicit = os.environ.get(CONFIG_ENV)
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg and os.path.isabs(xdg):
        return Path(xdg) / "lookup" / "config.json"
    return Path.home() / ".config" / "lookup" / "config.json"


def cache_dir() -> Path:
    """Resolve the cache directory. Creates nothing on disk."""
    explicit = os.environ.get(CACHE_ENV)
    if explicit:
        return Path(explicit)
    xdg = os.environ.get("XDG_CACHE_HOME")
    if xdg and os.path.isabs(xdg):
        return Path(xdg) / "lookup"
    return Path.home() / ".cache" / "lookup"


def _parse_dictionaries(value) -> tuple[tuple[str, bool], ...]:
    if not isinstance(value, list):
        return ()
    out = []
    seen = set()
    for entry in value:
        if not isinstance(entry, dict):
            continue
        ident = entry.get("id")
        if not isinstance(ident, str) or not 1 <= len(ident) <= MAX_ID_CHARS or "\x00" in ident:
            continue
        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            continue
        if ident in seen:
            continue
        seen.add(ident)
        out.append((ident, enabled))
    return tuple(out)


def _parse_clients(value) -> tuple[str, ...] | None:
    if not isinstance(value, list):
        return None
    good = tuple(c for c in value if isinstance(c, str) and _CLIENT_RE.match(c))
    return good or None


def load(path=None) -> Config:
    """Read the config; any problem yields defaults for the affected part."""
    target = Path(path) if path is not None else config_path()
    try:
        with open(target, "rb") as fh:
            raw = fh.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            return Config()
        data = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError, RecursionError):
        return Config()
    if not isinstance(data, dict):
        return Config()
    online = data.get("online", True)
    return Config(
        dictionaries=_parse_dictionaries(data.get("dictionaries")),
        online=online if isinstance(online, bool) else True,
        clients=_parse_clients(data.get("clients")),
    )
