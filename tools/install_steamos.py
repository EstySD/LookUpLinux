#!/usr/bin/env python3
"""Install, inspect or remove a portable SteamOS Desktop Mode bundle without root."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from lookup import config,portable


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    install=commands.add_parser('install',help='Install from a source checkout or a bundle')
    install.add_argument('--source',type=Path,help='Source checkout containing lookup/')
    install.add_argument('--bundle',type=Path,help='Bounded tar.gz runtime bundle')
    install.add_argument('--home',type=Path,help='Override home directory (tests only)')
    uninstall=commands.add_parser('uninstall',help='Remove owned files, preserve user data')
    uninstall.add_argument('--home',type=Path)
    status=commands.add_parser('status',help='Report owned install paths as JSON')
    status.add_argument('--home',type=Path)
    args=parser.parse_args(argv)
    home=args.home
    try:
        if args.command=='install':
            paths=portable.install(source=args.source or (None if args.bundle else ROOT),
                                   bundle=args.bundle,home=home,shortcut=config.load().shortcut)
            print('Installed portable LookUp Linux in '+str(paths['app']))
            print('Launch from the applications menu or run ~/.local/bin/lookup --app')
            try:
                enabled=subprocess.run(['systemctl','--user','enable','--now',
                                        portable.SERVICE],stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL,timeout=8,check=False).returncode==0
            except (OSError,subprocess.TimeoutExpired):
                enabled=False
            print('Gaming daemon autostart: '+
                  ('enabled.' if enabled else 'not enabled automatically; run systemctl --user enable --now '+portable.SERVICE))
            return 0
        if args.command=='uninstall':
            location=portable.uninstall(home=home)
            print('Removed portable files from '+str(location['app']))
            print('Words, cards, dictionaries and settings were preserved.')
            return 0
        print(json.dumps(portable.status(home=home),indent=2,sort_keys=True))
        return 0
    except portable.PortableError as error:
        print('install_steamos: '+error.reason,file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
