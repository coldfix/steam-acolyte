from .util import read_file, write_file, join_args, subkey_lookup as lookup

import vdf
from PyQt5.QtCore import QThread, pyqtSignal

import fcntl
import os
from time import sleep


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
        steam_config = lookup(reg_data, r'Registry\HKCU\Software\Valve\Steam')
        return steam_config.get('AutoLoginUser', '')

    def set_last_user(self, username):
        reg_file = os.path.expanduser('~/.steam/registry.vdf')
        reg_data = vdf.loads(read_file(reg_file))
        steam_config = lookup(reg_data, r'Registry\HKCU\Software\Valve\Steam')
        steam_config['AutoLoginUser'] = username
        steam_config['RememberPassword'] = '1'
        reg_data = vdf.dumps(reg_data, pretty=True)
        with open(reg_file, 'wt') as f:
            f.write(reg_data)

    PID_FILE = '~/.steam/steam.pid'
    PIPE_FILE = '~/.steam/steam.pipe'

    def _is_steam_pid_valid(self):
        """Check if the steam.pid file designates a running process."""
        return is_process_running(self._read_steam_pid())

    def _read_steam_pid(self):
        pidfile = os.path.expanduser(self.PID_FILE)
        pidtext = read_file(pidfile)
        if not pidtext:
            return False
        return int(pidtext)

    def _set_steam_pid(self):
        pidfile = os.path.expanduser(self.PID_FILE)
        pidtext = str(os.getpid())
        write_file(pidfile, pidtext)

    _pipe_fd = -1
    _thread = None

    def _connect(self):
        self._pipe_fd = self._open_pipe_for_writing(self.PIPE_FILE)
        return self._pipe_fd != -1

    def _listen(self):
        self._pipe_fd = self._open_pipe_for_reading(self.PIPE_FILE)
        self._thread = FileReaderThread(self._pipe_fd)
        self._thread.line_received.connect(self.command_received.emit)
        self._thread.start()
        return True

    def send(self, args):
        text = join_args(args) + '\n'
        os.write(self._pipe_fd, text.encode('utf-8'))

    def unlock(self):
        if self._thread is not None:
            self._thread.stop()
            self._thread = None
        if self._pipe_fd != -1:
            os.close(self._pipe_fd)
            self._pipe_fd = -1
        if self._lock_fd != -1:
            os.close(self._lock_fd)
            self._lock_fd = -1

    def ensure_single_acolyte_instance(self):
        """Ensure that we are the only acolyte instance. Return true if we are
        the first instance, false if another acolyte instance is running."""
        pid_file = os.path.join(self.root, 'acolyte', 'acolyte.lock')
        self._lock_fd = os.open(pid_file, os.O_WRONLY | os.O_CREAT, 0o644)
        try:
            fcntl.lockf(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except IOError:
            return False

    def wait_for_steam_exit(self):
        """Wait until steam is closed."""
        pid = self._read_steam_pid()
        while is_process_running(pid):
            sleep(0.010)

    def _open_pipe_for_writing(self, name):
        """Open steam.pipe as a writer (client)."""
        mode = os.O_WRONLY | os.O_NONBLOCK
        path = os.path.expanduser(name)
        return os.open(path, mode)

    def _open_pipe_for_reading(self, name):
        """Open steam.pipe as a reader (server)."""
        path = os.path.expanduser(name)
        dirname = os.path.dirname(path)
        os.makedirs(dirname, 0o755, exist_ok=True)
        try:
            os.mkfifo(path, 0o644)
        except FileExistsError:
            pass
        # You may think O_RDWR is awkward here, but it seems to be the only
        # way to have a nonblocking open() combined with blocking read()!
        # With mode=O_RDONLY, the open call would block, waiting for a
        # writer. It can be made nonblocking using mode=O_RDONLY|O_NONBLOCK,
        # but then the pipe would be always ready to read, returning empty
        # strings upon read()-ing (even if fcntl()-ing away O_NONBLOCK).
        # See also: https://stackoverflow.com/a/580057/650222.
        # Additionally, this makes it possible for us to send data into the
        # pipe to wake up the reader thread!
        return os.open(path, os.O_RDWR)


class FileReaderThread(QThread):

    """Read a file asynchronously. Emit signal whenever a new line becomes
    available."""

    line_received = pyqtSignal(str)

    def __init__(self, fd):
        super().__init__()
        self._fd = fd
        self._exit = False

    def run(self):
        # `dup()`-ing the file descriptor serves two purposes here:
        # - to leave the `self._fd` open when `f` reaches its end of life
        # - to allow writing to `self._fd` without blocking from the main thread
        with os.fdopen(os.dup(self._fd)) as f:
            for line in f:
                line = line.rstrip('\n')
                if line:
                    self.line_received.emit(line)
                elif self._exit:
                    return

    def stop(self):
        self._exit = True
        # We have to wake up the reader thread by sending an empty line. I
        # first tried to close the file directly, but it turns out this blocks
        # the main thread and does not wake up the reader thread. Note that
        # this operation would block if we did dup() the file descriptor:
        os.write(self._fd, b"\n")
        self.wait()


def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False
