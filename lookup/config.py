"""config.json reader and config/cache directory resolvers (D-03, D-13, D-17).

The file is user-editable (and later written by the settings window), so every
key is validated on its own and damage degrades to defaults. Loading/resolving
paths creates nothing; explicit saves are private and atomic. No logging (V7).
"""
import json
import os
import re
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

CONFIG_ENV = "LOOKUP_CONFIG"
CACHE_ENV = "LOOKUP_CACHE"
MAX_CONFIG_BYTES = 1 << 20
MAX_ID_CHARS = 512
POPUP_FIELDS = ('popup_show_context','popup_show_meaning','popup_expand_articles')

# A client name ends up in a request URL (T-02-08): keep it boring.
_CLIENT_RE = re.compile(r"[A-Za-z0-9._-]{1,32}\Z")


@dataclass(frozen=True)
class Config:
    # (dictionary id, enabled) in the user's order; the id is only ever compared
    # with discovered dictionaries by the search layer, never joined to a path.
    dictionaries: tuple[tuple[str, bool], ...] = ()
    online: bool = True
    clients: tuple[str, ...] | None = None
    shortcut: str = 'Meta+Shift+D'
    popup_timeout: int = 20
    autostart: bool = True
    popup_show_context: bool = False
    popup_show_meaning: bool = True
    popup_expand_articles: bool = False


class ConfigError(ValueError):
    def __init__(self, reason):
        self.reason = reason if reason in ('invalid_value','invalid_file','unavailable') else 'invalid_value'
        super().__init__(self.reason)


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


def _read(target, strict=False):
    try:
        with open(target, "rb") as fh:
            raw = fh.read(MAX_CONFIG_BYTES + 1)
        if len(raw) > MAX_CONFIG_BYTES:
            raise ValueError
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data,dict):
            raise ValueError
        return data
    except FileNotFoundError:
        return {}
    except OSError:
        if strict:
            raise ConfigError('unavailable') from None
    except (ValueError, UnicodeError, RecursionError):
        if strict:
            raise ConfigError('invalid_file') from None
    return {}


def _valid_scalar(key, value):
    if key in ('online','autostart') + POPUP_FIELDS:
        return isinstance(value,bool)
    if key == 'popup_timeout':
        return isinstance(value,int) and not isinstance(value,bool) and 1 <= value <= 300
    if key == 'shortcut':
        return (isinstance(value,str) and 1 <= len(value) <= 128 and value == value.strip()
                and not any(unicodedata.category(c).startswith('C') for c in value))
    return False


def _from_data(data):
    online = data.get("online", True)
    defaults = Config()
    return Config(
        dictionaries=_parse_dictionaries(data.get("dictionaries")),
        online=online if isinstance(online, bool) else True,
        clients=_parse_clients(data.get("clients")),
        **{key:data[key] if key in data and _valid_scalar(key,data[key]) else getattr(defaults,key)
           for key in ('shortcut','popup_timeout','autostart') + POPUP_FIELDS},
    )


def load(path=None) -> Config:
    """Read the config; any problem yields defaults for the affected part."""
    target = Path(path) if path is not None else config_path()
    return _from_data(_read(target))


def save(changes, path=None, *, retain_missing=True) -> Config:
    """Merge edited fields; transaction rollback can restore an exact ID set.

    Ordinary edits retain configured-but-missing dictionaries. Unrelated keys
    and clients remain untouched in both modes.
    """
    if not isinstance(changes,dict) or not isinstance(retain_missing,bool):
        raise ConfigError('invalid_value')
    for key,value in changes.items():
        if key == 'dictionaries':
            valid = isinstance(value,list) and len(_parse_dictionaries(value)) == len(value)
        elif key == 'clients':
            valid = value is None or (isinstance(value,list) and
                    all(isinstance(v,str) and _CLIENT_RE.fullmatch(v) for v in value))
        else:
            valid = _valid_scalar(key,value)
        if not valid:
            raise ConfigError('invalid_value')
    target = Path(path) if path is not None else config_path()
    data = _read(target,strict=True)
    edited = dict(changes)
    if 'dictionaries' in edited and retain_missing:
        dictionaries = list(edited['dictionaries'])
        included = {entry['id'] for entry in dictionaries}
        dictionaries.extend(dict(id=ident,enabled=enabled)
                            for ident,enabled in _parse_dictionaries(data.get('dictionaries')) if ident not in included)
        edited['dictionaries'] = dictionaries
    data.update(edited)
    temporary = None
    try:
        raw = (json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8')
        if len(raw) > MAX_CONFIG_BYTES:
            raise ConfigError('invalid_value')
        target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with tempfile.NamedTemporaryFile(mode='wb',dir=target.parent,prefix='.'+target.name+'.',
                                         suffix='.tmp',delete=False) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary,0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary,target)
    except OSError:
        raise ConfigError('unavailable') from None
    except (TypeError,ValueError,UnicodeError,RecursionError):
        raise ConfigError('invalid_value') from None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    return _from_data(data)
