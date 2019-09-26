import vdf

import os
import sys
from shutil import copyfile


class SteamUser:

    def __init__(self, steam_id, account_name, persona_name, timestamp):
        self.steam_id = steam_id
        self.account_name = account_name
        self.persona_name = persona_name
        self.timestamp = timestamp


class Steam:

    # I tested this script on an ubuntu and archlinux machine, where I found
    # the steam config and program files in different locations. In both cases
    # there was also a path/symlink that pointed to the correct location, but
    # since I don't know whether this is true for all distributions and steam
    # versions, we go through all known prefixes anyway:
    #
    #             common name           ubuntu            archlinux
    #   config    ~/.steam/steam@   ->  ~/.steam/steam    ~/.local/share/Steam
    #   data      ~/.steam/root@    ->  ~/.steam          ~/.local/share/Steam

    STEAM_ROOT_PATH = [
        '~/.local/share/Steam',
        '~/.steam/steam',
        '~/.steam/root',
        '~/.steam',
    ]

    def __init__(self, root=None, exe=None, data=None):
        self.root = root or self.find_root()
        self.data = data or self.find_data()
        self.exe = exe or self.find_exe()

    def store_login_cookie(self):
        username = self.get_last_user()
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        configpath = os.path.join(self.root, 'config', 'config.vdf')
        os.makedirs(os.path.dirname(userpath), exist_ok=True)
        copyfile(configpath, userpath)

    def remove_login_cookie(self, username):
        userpath = os.path.join(self.root, 'acolyte', username, 'config.vdf')
        if os.path.isfile(userpath):
            os.remove(userpath)

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

    def get_last_user(self):
        if sys.platform == 'win32':
            return read_steam_registry_value("AutoLoginUser")
        else:
            reg_file = os.path.expanduser('~/.steam/registry.vdf')
            reg_data = vdf.loads(read_file(reg_file))
            steam_config = reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
            return steam_config['AutoLoginUser']

    def set_last_user(self, username):
        if sys.platform == 'win32':
            import winreg as reg
            with reg.CreateKey(
                    reg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
                reg.SetValueEx(key, "AutoLoginUser", 0, reg.REG_SZ, username)
                reg.SetValueEx(key, "RememberPassword", 0, reg.REG_DWORD, 1)
        else:
            reg_file = os.path.expanduser('~/.steam/registry.vdf')
            reg_data = vdf.loads(read_file(reg_file))
            steam_config = reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
            steam_config['AutoLoginUser'] = username
            steam_config['RememberPassword'] = '1'
            reg_data = vdf.dumps(reg_data, pretty=True)
            with open(reg_file, 'wt') as f:
                f.write(reg_data)

    def run(self, args=()):
        """Run steam."""
        import subprocess
        subprocess.call([self.exe, *args])

    def read_config(self, filename='config.vdf'):
        """Read steam config.vdf file."""
        conf = os.path.join(self.root, 'config', filename)
        text = read_file(conf)
        return vdf.loads(text)

    @classmethod
    def find_root(cls):
        """Locate and return the root path for the steam user config."""
        if sys.platform == 'win32':
            return read_steam_registry_value("SteamPath")
        else:
            # On arch and ubuntu, this is in '~/.steam/steam/', but as I'm not
            # sure that's the case everywhere, we search through all known
            # prefixes for good measure:
            for root in cls.STEAM_ROOT_PATH:
                root = os.path.expanduser(root)
                conf = os.path.join(root, 'config', 'config.vdf')
                if os.path.isdir(root) and os.path.isfile(conf):
                    return root
        raise RuntimeError("""Unable to find steam user path!""")

    @classmethod
    def find_data(cls):
        """Locate and return the root path for the steam program files."""
        if sys.platform == 'win32':
            return read_steam_registry_value("SteamPath")
        else:
            # On arch and ubuntu, this is in '~/.steam/root/', but as I'm not
            # sure that's the case everywhere, we search through all known
            # prefixes for good measure:
            for root in cls.STEAM_ROOT_PATH:
                root = os.path.expanduser(root)
                data = os.path.join(root, 'clientui', 'images', 'icons')
                if os.path.isdir(root) and os.path.isdir(data):
                    return root
        raise RuntimeError("""Unable to find steam program data!""")

    @classmethod
    def find_exe(cls):
        if sys.platform == 'win32':
            return read_steam_registry_value("SteamExe")
        else:
            return 'steam'


def read_steam_registry_value(value_name):
    import winreg
    with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
        return winreg.QueryValueEx(key, value_name)[0]


def read_file(filename):
    """Read full contents of given file."""
    with open(filename) as f:
        return f.read()
