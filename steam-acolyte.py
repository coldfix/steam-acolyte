#! /usr/bin/env python
"""
A lightweight steam account manager and switcher.

Usage:
    steam-acolyte [options] store
    steam-acolyte [options] switch <USER>
    steam-acolyte [options] start <USER>

Options:
    -r ROOT, --root ROOT        Steam root path
"""

import vdf
from docopt import docopt

import os
import sys
from shutil import copyfile


STEAM_ROOT_PATH = [
    '~/.local/share/Steam',
    '~/.steam/root',
    '~/.steam',
]


def main(args):
    opts = docopt(__doc__, args)
    root = opts['--root'] or find_steam_root()
    if root is None:
        print("""Unable to find steam user path!""", file=sys.stderr)
        return 1
    if opts['store']:
        store_login_cookie(root)
    if opts['switch']:
        switch_user(root, opts['<USER>'])
    if opts['start']:
        switch_user(root, opts['<USER>'])
        run_steam()


def store_login_cookie(root):
    username = get_last_user(root)
    user_id = get_user_id(root, username)
    userpath = os.path.join(root, 'acolyte', user_id, 'config.vdf')
    configpath = os.path.join(root, 'config', 'config.vdf')
    os.makedirs(os.path.dirname(userpath), exist_ok=True)
    copyfile(configpath, userpath)


def switch_user(root, username):
    """Switch login config to given user. Do not use this while steam is
    running."""
    set_last_user(root, username)
    user_id = get_user_id(root, username)
    userpath = os.path.join(root, 'acolyte', user_id, 'config.vdf')
    configpath = os.path.join(root, 'config', 'config.vdf')
    if not os.path.isfile(userpath):
        print(f"No stored config found for {username!r}", file=sys.stderr)
        return False
    copyfile(userpath, configpath)
    return True


def get_user_id(root, username):
    config = read_steam_config(root)
    steam = config['InstallConfigStore']['Software']['Valve']['Steam']
    accounts = steam['Accounts']
    return accounts[username]['SteamID']


def get_last_user(root):
    # Only linux (stored in registry on windows):
    reg_file = os.path.expanduser('~/.steam/registry.vdf')
    reg_data = vdf.loads(read_file(reg_file))
    steam_config = reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
    return steam_config['AutoLoginUser']


def set_last_user(root, username):
    reg_file = os.path.expanduser('~/.steam/registry.vdf')
    reg_data = vdf.loads(read_file(reg_file))
    steam_config = reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
    steam_config['AutoLoginUser'] = username
    steam_config['RememberPassword'] = '1'
    reg_data = vdf.dumps(reg_data, pretty=True)
    with open(reg_file, 'wt') as f:
        f.write(reg_data)


def run_steam(args=()):
    """Run steam."""
    import subprocess
    subprocess.call(['steam', *args])


def read_steam_config(root):
    """Read steam config.vdf file."""
    conf = os.path.join(root, 'config', 'config.vdf')
    text = read_file(conf)
    return vdf.loads(text)


def find_steam_root():
    """Locate and return the root path for the steam program files and user
    configuration."""
    for root in STEAM_ROOT_PATH:
        root = os.path.expanduser(root)
        conf = os.path.join(root, 'config', 'config.vdf')
        if os.path.isdir(root) and os.path.isfile(conf):
            return root


def read_file(filename):
    """Read full contents of given file."""
    with open(filename) as f:
        return f.read()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
