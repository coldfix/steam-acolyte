from .util import read_file

import vdf

import os


class SteamLinux:

    """Linux specific methods for the interaction with steam. This implements
    the SteamBase interface and is used as a mixin for Steam."""

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

    @classmethod
    def find_root(cls):
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
        return 'steam'

    def get_last_user(self):
        reg_file = os.path.expanduser('~/.steam/registry.vdf')
        reg_data = vdf.loads(read_file(reg_file))
        steam_config = \
            reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
        return steam_config['AutoLoginUser']

    def set_last_user(self, username):
        reg_file = os.path.expanduser('~/.steam/registry.vdf')
        reg_data = vdf.loads(read_file(reg_file))
        steam_config = \
            reg_data['Registry']['HKCU']['Software']['Valve']['Steam']
        steam_config['AutoLoginUser'] = username
        steam_config['RememberPassword'] = '1'
        reg_data = vdf.dumps(reg_data, pretty=True)
        with open(reg_file, 'wt') as f:
            f.write(reg_data)
