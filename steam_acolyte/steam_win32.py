from .util import join_args, func_lookup

from PyQt5.QtCore import QWinEventNotifier

from ctypes import wintypes, windll, WinError
import os
from types import SimpleNamespace
import winreg as reg


# Synchronization Object Security and Access Rights:
# https://docs.microsoft.com/en-us/windows/win32/sync/synchronization-object-security-and-access-rights
SYNCHRONIZE        = 0x00100000
EVENT_MODIFY_STATE = 0x00000002

# WaitForSingleObject return values:
WAIT_TIMEOUT       = 0x00000102


winapi = SimpleNamespace(**func_lookup(windll.kernel32, wintypes, """
    BOOL CloseHandle(HANDLE);

    HANDLE CreateEventA(LPCVOID, BOOL, BOOL, LPCSTR);
    HANDLE OpenEventA(DWORD, BOOL, LPCSTR);
    BOOL SetEvent(BOOL);

    DWORD WaitForSingleObject(HANDLE, DWORD);

    HANDLE OpenProcess(DWORD, BOOL, DWORD);
"""))


class SteamWin32:

    """Windows specific methods for the interaction with steam. This implements
    the SteamBase interface and is used as a mixin for Steam."""

    REG_KEY = r'SOFTWARE\WOW6432Node\Valve\Steam'
    EVENT_NAME = rb'Global\Valve_SteamIPC_Class'
    _event = None

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

    def _is_steam_pid_valid(self):
        with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, self.REG_KEY) as key:
            pid = reg.QueryValueEx(key, 'SteamPID')[0]
            return pid != 0 and IsProcessRunning(pid)

    def _set_steam_pid(self):
        with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, self.REG_KEY) as key:
            reg.SetValueEx(key, 'SteamPID', 0, reg.REG_DWORD, os.getpid())

    def _connect(self):
        self._event = winapi.OpenEventA(
            EVENT_MODIFY_STATE, False, self.EVENT_NAME)
        return bool(self._event)

    def _listen(self):
        self._event = winapi.CreateEventA(
            None, False, False, self.EVENT_NAME)
        if not self._event:
            raise WinError()
        self._wait = QWinEventNotifier(self._event)
        self._wait.activated.connect(self._fetch)

    def _fetch(self):
        with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, self.REG_KEY) as key:
            cmdl = reg.QueryValueEx(key, 'TempAppCmdLine')[0]
            reg.SetValueEx(key, 'TempAppCmdLine', 0, reg.REG_SZ, '')
        self.command_received.emit(cmdl)

    def send(self, args):
        with reg.CreateKey(reg.HKEY_LOCAL_MACHINE, self.REG_KEY) as key:
            cmdl = join_args(args)
            reg.SetValueEx(key, 'TempAppCmdLine', 0, reg.REG_SZ, cmdl)
        if not winapi.SetEvent(self._event):
            raise WinError()

    def unlock(self):
        if self._event:
            winapi.CloseHandle(self._event)
            self._event = None


def read_steam_registry_value(value_name):
    with reg.OpenKey(reg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
        return reg.QueryValueEx(key, value_name)[0]


def IsProcessRunning(pid):
    # Steam seems to use ProcessIdToSessionId to distinguish the case where the
    # other steam instance is running in the same user session, but I don't know
    # how it would handle this case, so let's just check if another steam
    # process is running at all:.
    handle = winapi.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return False
    status = winapi.WaitForSingleObject(handle, 0)
    winapi.CloseHandle(handle)
    return status == WAIT_TIMEOUT
