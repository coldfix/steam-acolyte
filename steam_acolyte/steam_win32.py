from .util import join_args, import_declarations, Tracer

from PyQt5.QtCore import QWinEventNotifier

from ctypes import wintypes, windll, WinError, GetLastError
import os
from types import SimpleNamespace
import winreg as reg

# Basic constants:
INFINITE           = 0xFFFFFFFF

# Error codes:
# https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
ERROR_ALREADY_EXISTS = 183

# Synchronization Object Security and Access Rights:
# https://docs.microsoft.com/en-us/windows/win32/sync/synchronization-object-security-and-access-rights
SYNCHRONIZE        = 0x00100000
EVENT_MODIFY_STATE = 0x00000002

# WaitForSingleObject return values:
WAIT_TIMEOUT       = 0x00000102


winapi = SimpleNamespace(**import_declarations(windll.kernel32, wintypes, """
    BOOL CloseHandle(HANDLE);

    HANDLE CreateEventA(LPCVOID, BOOL, BOOL, LPCSTR);
    HANDLE OpenEventA(DWORD, BOOL, LPCSTR);
    BOOL SetEvent(BOOL);
    HANDLE CreateMutexA(LPCVOID, BOOL, LPCSTR);

    DWORD WaitForSingleObject(HANDLE, DWORD);

    HANDLE OpenProcess(DWORD, BOOL, DWORD);
"""))


trace = Tracer(__name__)


class SteamWin32:

    """Windows specific methods for the interaction with steam. This implements
    the SteamBase interface and is used as a mixin for Steam."""

    USER_KEY = r"SOFTWARE\Valve\Steam"
    IPC_KEY = r'SOFTWARE\WOW6432Node\Valve\Steam'
    EVENT_NAME = rb'Global\Valve_SteamIPC_Class'
    _event = None
    _mutex = None

    def __init__(self, prefix=None, root=None, exe=None):
        super().__init__()
        self._user_key = reg.CreateKey(reg.HKEY_CURRENT_USER, self.USER_KEY)
        self._ipc_key = reg.CreateKey(reg.HKEY_LOCAL_MACHINE, self.IPC_KEY)
        if prefix and root and prefix != root:
            raise RuntimeError(
                "There is no distinction between --prefix and --root on "
                "windows. Please pass only --prefix!")
        self.prefix = prefix or root or self.find_root()
        self.root = self.prefix
        self.exe = exe or self.find_exe()
        self.steam_config = os.path.join(self.root, 'config')
        self.acolyte_data = os.path.join(self.root, 'acolyte')

    def __del__(self):
        self._user_key.Close()
        self._ipc_key.Close()

    def find_root(self):
        return reg.QueryValueEx(self._user_key, "SteamPath")[0]

    def find_exe(self):
        return reg.QueryValueEx(self._user_key, "SteamExe")[0]

    @trace.method
    def get_last_user(self):
        return reg.QueryValueEx(self._user_key, "AutoLoginUser")[0]

    @trace.method
    def set_last_user(self, username):
        reg.SetValueEx(self._user_key, "AutoLoginUser", 0, reg.REG_SZ, username)
        reg.SetValueEx(self._user_key, "RememberPassword", 0, reg.REG_DWORD, 1)

    @trace.method
    def _is_steam_pid_valid(self):
        pid = reg.QueryValueEx(self._ipc_key, 'SteamPID')[0]
        return pid and is_process_running(pid)

    @trace.method
    def _set_steam_pid(self):
        reg.SetValueEx(self._ipc_key, 'SteamPID', 0, reg.REG_DWORD, os.getpid())

    @trace.method
    def _unset_steam_pid(self):
        reg.SetValueEx(self._ipc_key, 'SteamPID', 0, reg.REG_DWORD, 0)

    @trace.method
    def _connect(self):
        self._event = winapi.OpenEventA(
            EVENT_MODIFY_STATE, False, self.EVENT_NAME)
        return bool(self._event)

    @trace.method
    def _listen(self):
        self._has_steam_lock = True
        self._event = winapi.CreateEventA(
            None, False, False, self.EVENT_NAME)
        if not self._event:
            raise WinError()
        self._wait = QWinEventNotifier(self._event)
        self._wait.activated.connect(self._fetch)

    @trace.method
    def _fetch(self):
        cmdl = reg.QueryValueEx(self._ipc_key, 'TempAppCmdLine')[0]
        reg.SetValueEx(self._ipc_key, 'TempAppCmdLine', 0, reg.REG_SZ, '')
        self.command_received.emit(cmdl)

    @trace.method
    def _send(self, args):
        cmdl = join_args(args)
        reg.SetValueEx(self._ipc_key, 'TempAppCmdLine', 0, reg.REG_SZ, cmdl)
        if not winapi.SetEvent(self._event):
            raise WinError()

    @trace.method
    def unlock(self):
        if self._event:
            self._unset_steam_pid()
            winapi.CloseHandle(self._event)
            self._event = None
            self._has_steam_lock = False

    @trace.method
    def ensure_single_acolyte_instance(self):
        """Ensure that we are the only acolyte instance."""
        if self._mutex is not None:
            return True
        name = b'acolyte-instance-lock-{4F0BE4F0-52F2-4A7F-BEAB-D02807303CBF}'
        self._mutex = winapi.CreateMutexA(None, False, name)
        if self._mutex is None:
            raise WinError()
        if GetLastError() == ERROR_ALREADY_EXISTS:
            self.release_acolyte_instance_lock()
            return False
        self._has_acolyte_lock = True
        return True

    @trace.method
    def release_acolyte_instance_lock(self):
        if self._mutex:
            winapi.CloseHandle(self._mutex)
            self._mutex = None
            self._has_acolyte_lock = False

    @trace.method
    def wait_for_steam_exit(self):
        """Wait until steam is closed."""
        pid = reg.QueryValueEx(self._ipc_key, 'SteamPID')[0]
        return wait_process(pid)


def is_process_running(pid):
    """Check if a process with the given PID is currently running."""
    # Steam seems to use ProcessIdToSessionId to distinguish the case where the
    # other steam instance is running in the same user session, but I don't know
    # how it would handle this case, so let's just check if another steam
    # process is running at all:
    return not wait_process(pid, 0)


def wait_process(pid, timeout=INFINITE):
    """Wait until process with the given PID exits or the timeout expires.
    Returns ``True`` if the process has exited before this function was called
    or the timeout expires."""
    handle = winapi.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return True
    status = winapi.WaitForSingleObject(handle, timeout)
    winapi.CloseHandle(handle)
    return status != WAIT_TIMEOUT
