from .util import read_file, write_file, subkey_lookup

from PyQt5.QtCore import QObject, pyqtSignal, QProcess
import vdf

import os
import sys
import shlex
from time import sleep
from shutil import copyfile
from abc import abstractmethod

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


class SteamBase:

    """This defines the methods that need to be provided by the platform
    specific implementations (SteamLinux/SteamWin32)."""

    @abstractmethod
    def find_root(cls):
        """Locate and return the root path for the steam user config."""

    @abstractmethod
    def find_exe(cls):
        """Return name of the steam executable."""

    @abstractmethod
    def get_last_user(self):
        """Return username which was last logged on."""

    @abstractmethod
    def set_last_user(self, username):
        """Tell steam to login given user at next start."""

    # IPC:

    @abstractmethod
    def _is_steam_pid_valid(self):
        """Check if the saved steam PID file belongs to a running process."""

    @abstractmethod
    def _set_steam_pid(self):
        """Save current process ID as the last steam PID."""

    @abstractmethod
    def _connect(self) -> bool:
        """Connect to an already running steam instance. Returns true if
        successful. Called after ``_is_steam_pid_valid()`` returned true."""

    @abstractmethod
    def _listen(self):
        """Start listening to messages from other steam processes that want to
        communicate their command line to us."""

    @abstractmethod
    def _send(self, args: list):
        """Send command line to connected steam instance. Only valid if
        previously ``_connect()``-ed."""

    @abstractmethod
    def unlock(self):
        """Close connection to other steam instance, or stop listening."""

    @abstractmethod
    def ensure_single_acolyte_instance(self):
        """Ensure that we are the only acolyte instance."""

    @abstractmethod
    def release_acolyte_instance_lock(self):
        """Allow other acolyte instances to run again."""

    @abstractmethod
    def wait_for_steam_exit(self):
        """Wait until steam is closed."""


class Steam(SteamImpl, SteamBase, QObject):

    """This class allows various interactions with steam. Note that many of
    the methods are only safe to use while steam is not running."""

    command_received = pyqtSignal(str)

    def __init__(self, root=None, exe=None, args=()):
        super().__init__()
        self.root = root or self.find_root()
        self.exe = exe or self.find_exe()
        self.command_received.connect(self._steam_cmdl_received)
        self.args = args

    def __del__(self):
        self.unlock()
        if hasattr(SteamImpl, '__del__'):
            SteamImpl.__del__(self)

    def wait_for_lock(self):
        """Wait until steam has exited, and lock can be acquired. May be
        called only if we are the first acolyte instance."""
        self.unlock()
        while not self.lock()[1]:
            self.unlock()
            self.wait_for_steam_exit()

    def lock(self, args=None):
        """
        Engage in steam's single instance locking mechanism.

        This allows us to detect if steam is already running, and:

        - if so: notify it to go the foreground or start a requested app
        - if not: block it from running as long as we are active

        This is important because many of our operations are only safe to
        perform while steam is not running.

        Note that we also have an acolyte-specific instance lock that is
        devised to keep multiple instances from waiting in the background and
        successively opening windows after the previous one was closed. Only
        the first instance is allowed to acquire the steam lock and therefore
        perform operations or show a GUI.
        """
        # The loop is needed to deal with the race condition due a second
        # acolyte instance being scheduled after the first one acquires the
        # lock, but before it starts to listen, and therefore fails to connect
        # to the steam IPC:
        while True:
            first = self.ensure_single_acolyte_instance()
            if self._is_steam_pid_valid() and self._connect():
                if args is not None:
                    self._send([self.exe, *args])
                return (first, False)
            if first:
                self._set_steam_pid()
                self._listen()
                return (True, True)
            sleep(0.050)

    def _steam_cmdl_received(self, line):
        self.args = shlex.split(line.rstrip())[1:]

    def users(self):
        """Return a list of ``SteamUser``."""
        config = self.read_config('loginusers.vdf')
        users = subkey_lookup(config, r'users')
        return [
            SteamUser(uid, u['AccountName'], u['PersonaName'], u['Timestamp'])
            for uid, u in users.items()
        ]

    def store_login_cookie(self):
        username = self.get_last_user()
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        configpath = os.path.join(self.root, 'config', 'config.vdf')
        config = self.read_config('config.vdf')
        accounts = subkey_lookup(
            config, r'InstallConfigStore\Software\Valve\Steam\Accounts')
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
            for uid, info in subkey_lookup(loginusers, r'users').items()
            if info['AccountName'] != username
        }
        self.write_config('loginusers.vdf', loginusers)

        config = self.read_config('config.vdf')
        accounts = subkey_lookup(
            config, r'InstallConfigStore\Software\Valve\Steam\Accounts')
        accounts.pop(username, None)
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

    def run(self):
        """Run steam."""
        process = self._process = QProcess()
        process.setInputChannelMode(QProcess.ForwardedInputChannel)
        process.setProcessChannelMode(QProcess.ForwardedChannels)
        process.start(self.exe, self.args)
        return process

    def read_config(self, filename='config.vdf'):
        """Read steam config.vdf file."""
        conf = os.path.join(self.root, 'config', filename)
        text = read_file(conf)
        return vdf.loads(text) if text else {}

    def write_config(self, filename, data):
        conf = os.path.join(self.root, 'config', filename)
        text = vdf.dumps(data, pretty=True)
        write_file(conf, text)
