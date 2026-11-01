"""Install source launchers and the GNOME 46 bridge for the current user."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
UUID='lookup-linux@lookup.local'


def install():
    if sys.platform!='linux' or os.geteuid()==0:
        raise SystemExit('Run as your normal desktop user on Ubuntu, without sudo.')
    sys.path.insert(0,str(ROOT))
    from lookup import gnome,lifecycle
    if not gnome.active():raise SystemExit('Run from a GNOME Wayland desktop terminal.')
    from PyQt6 import QtDBus  # Validate the dependency before creating launchers.
    version=subprocess.check_output(['gnome-shell','--version'],text=True).strip()
    if not version.split()[-1].startswith('46.'):
        raise SystemExit('This bridge is currently tested with GNOME Shell 46 (Ubuntu 24.04).')
    data=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')
    if not data.is_absolute():raise SystemExit('XDG_DATA_HOME must be absolute.')
    destination=data/'gnome-shell/extensions'/UUID
    if destination.is_symlink():raise SystemExit('Refusing extension symlink.')
    if destination.exists():
        try:owned=json.loads((destination/'metadata.json').read_text())['uuid']==UUID
        except (OSError,ValueError,KeyError):owned=False
        if not owned:raise SystemExit('Extension directory is not owned by LookUp Linux.')
    destination.mkdir(parents=True,exist_ok=True)
    for name in ('metadata.json','extension.js'):
        target=destination/name
        if target.is_symlink():raise SystemExit('Refusing extension file symlink.')
        target.write_bytes((ROOT/'packaging/gnome'/name).read_bytes().replace(b'\r\n',b'\n'))
    schemas=destination/'schemas'
    if schemas.is_symlink():raise SystemExit('Refusing schema directory symlink.')
    schemas.mkdir(exist_ok=True)
    schema='org.gnome.shell.extensions.lookup-linux.gschema.xml'
    if (schemas/schema).is_symlink() or (schemas/'gschemas.compiled').is_symlink():
        raise SystemExit('Refusing schema file symlink.')
    (schemas/schema).write_bytes((ROOT/'packaging/gnome/schemas'/schema).read_bytes())
    subprocess.run(['glib-compile-schemas',str(schemas)],check=True)
    lifecycle.ensure_entries(directory=ROOT)
    # The extension list belongs to GNOME; enabling preserves the other entries.
    try:enabled=subprocess.run(['gnome-extensions','enable',UUID],check=False,timeout=10).returncode==0
    except subprocess.TimeoutExpired:enabled=False
    print('Installed user launchers and GNOME bridge in '+str(destination))
    if not enabled:print('Log out and log in, then run: gnome-extensions enable '+UUID)
    else:print('If this is an update, log out and log in to load the new bridge.')
    print('Start: cd '+str(ROOT)+' && python3 -m lookup --app')


if __name__=='__main__':install()
