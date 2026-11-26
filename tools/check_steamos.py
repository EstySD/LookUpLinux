#!/usr/bin/env python3
"""Read-only SteamOS session report. Never reads history, screenshots or queries."""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from lookup import platform,session


def _version(command,args):
    try:
        text=platform.run([command,*args],timeout=2,limit=4096).decode('utf-8','replace')
    except Exception:
        return None
    return text.strip()[:200] or None


def main():
    if os.name!='posix' or not hasattr(os,'getuid'):
        print(json.dumps({'error':'linux_only'},ensure_ascii=False))
        return 2
    report=session.report()
    report['versions']={
        'plasma':_version('plasmashell',['--version']),
        'kwin':_version('kwin_wayland',['--version']),
        'gamescope':_version('gamescope',['--version']),
    }
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
