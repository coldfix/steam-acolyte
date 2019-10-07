import winreg as reg


class SteamWin32:

    """Windows specific methods for the interaction with steam. This implements
    the SteamBase interface and is used as a mixin for Steam."""

    @classmethod
    def find_root(cls):
        return read_steam_registry_value("SteamPath")

    @classmethod
    def find_data(cls):
        return read_steam_registry_value("SteamPath")

    @classmethod
    def find_exe(cls):
        return read_steam_registry_value("SteamExe")

    def get_last_user(self):
        return read_steam_registry_value("AutoLoginUser")

    def set_last_user(self, username):
        with reg.CreateKey(
                reg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
            reg.SetValueEx(key, "AutoLoginUser", 0, reg.REG_SZ, username)
            reg.SetValueEx(key, "RememberPassword", 0, reg.REG_DWORD, 1)


def read_steam_registry_value(value_name):
    with reg.OpenKey(reg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
        return reg.QueryValueEx(key, value_name)[0]
