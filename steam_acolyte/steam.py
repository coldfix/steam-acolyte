from .util import read_file, write_file

import vdf

import os
import sys
from shutil import copyfile
from abc import abstractmethod, abstractclassmethod, ABCMeta

if sys.platform == 'win32':
    from .steam_win32 import SteamWin32 as SteamImpl
else:
    from .steam_linux import SteamLinux as SteamImpl


class SteamUser:

    def __init__(self, steam_id, account_name, persona_name, timestamp):
        self.steam_id = steam_id
        self.account_name = account_name
        self.persona_name = persona_name
        self.timestamp = timestamp


class SteamBase(metaclass=ABCMeta):

    """This defines the methods that need to be provided by the platform
    specific implementations (SteamLinux/SteamWin32)."""

    @abstractclassmethod
    def find_root(cls):
        """Locate and return the root path for the steam user config."""

    @abstractclassmethod
    def find_data(cls):
        """Locate and return the root path for the steam program files."""

    @abstractclassmethod
    def find_exe(cls):
        """Return name of the steam executable."""

    @abstractmethod
    def get_last_user(self):
        """Return username which was last logged on."""

    @abstractmethod
    def set_last_user(self, username):
        """Tell steam to login given user at next start."""


class Steam(SteamImpl, SteamBase):

    """This class allows various interactions with steam. Note that many of
    the methods are only safe to use while steam is not running."""

    def __init__(self, root=None, exe=None, data=None):
        self.root = root or self.find_root()
        self.data = data or self.find_data()
        self.exe = exe or self.find_exe()

    def users(self):
        """Return a list of ``SteamUser``."""
        users = self.read_config('loginusers.vdf')['users']
        return [
            SteamUser(uid, u['AccountName'], u['PersonaName'], u['Timestamp'])
            for uid, u in users.items()
        ]

    def store_login_cookie(self):
        username = self.get_last_user()
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        configpath = os.path.join(self.root, 'config', 'config.vdf')
        accounts = (
            self.read_config('config.vdf')
            ['InstallConfigStore']['Software']['Valve']['Steam']['Accounts'])
        if accounts.get(username):
            os.makedirs(os.path.dirname(userpath), exist_ok=True)
            copyfile(configpath, userpath)
        else:
            print("Not replacing login data for logged out user: {!r}"
                  .format(username))

    def remove_login_cookie(self, username):
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        if os.path.isfile(userpath):
            os.remove(userpath)

    def remove_user(self, username):
        self.remove_login_cookie(username)
        loginusers = self.read_config('loginusers.vdf')
        loginusers['users'] = {
            uid: info
            for uid, info in loginusers['users'].items()
            if info['AccountName'] != username
        }
        self.write_config('loginusers.vdf', loginusers)

        config = self.read_config('config.vdf')
        steam = config['InstallConfigStore']['Software']['Valve']['Steam']
        steam['Accounts'].pop(username, None)
        self.write_config('config.vdf', config)

    def has_cookie(self, username):
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        return bool(username) and os.path.isfile(userpath)

    def switch_user(self, username):
        """Switch login config to given user. Do not use this while steam is
        running."""
        self.set_last_user(username)
        if not username:
            return True
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        configpath = os.path.join(self.root, 'config', 'config.vdf')
        if not os.path.isfile(userpath):
            print("No stored config found for {!r}".format(username),
                  file=sys.stderr)
            return False
        copyfile(userpath, configpath)
        return True

    def run(self, args=()):
        """Run steam."""
        import subprocess
        subprocess.call([self.exe, *args])

    def read_config(self, filename='config.vdf'):
        """Read steam config.vdf file."""
        conf = os.path.join(self.root, 'config', filename)
        text = read_file(conf)
        return vdf.loads(text)

    def write_config(self, filename, data):
        conf = os.path.join(self.root, 'config', filename)
        text = vdf.dumps(data, pretty=True)
        write_file(conf, text)
