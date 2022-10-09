"""
A lightweight steam account manager and switcher.

Usage:
    steam-acolyte [options]
    steam-acolyte [options] store
    steam-acolyte [options] switch <USER>
    steam-acolyte [options] start <USER>

Options:
    -p PREFIX, --prefix PREFIX  Steam prefix (e.g. `~/.steam`). On linux, this
                                folder should contain files `registry.vdf`,
                                `steam.pid`, `steam.pipe`. On windows, it is
                                simply the steam program folder.

    -r ROOT, --root ROOT        Steam config root. On linux, defaults to
                                `PREFIX/steam`. On windows this is the same as
                                `PREFIX`. In both cases, this folder should
                                contain a subfolder `config` with files
                                `config.vdf` and `loginusers.vdf`.
                                Usually, you don't need to change this path as
                                it will be set automatically from --prefix.

    -e EXE, --exe EXE           Set steam executable path and/or name

    -v, --verbose               Increase verbosity (debug)

    -l FILE, --logfile FILE     Log steam output to this file
"""

from steam_acolyte import __version__
from steam_acolyte.steam import Steam

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from docopt import docopt

import logging.config
import sys


def main(args=None):
    app = QApplication([])
    opts = docopt(__doc__, args, version=__version__)
    level = 'DEBUG' if opts['--verbose'] else 'INFO'
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'plain':  {'format': '%(message)s'},
            'detail': {'format': (
                '%(levelname)s [%(asctime)s] %(name)s: %(message)s')},
        },
        'handlers': {
            'error': {'class': 'logging.StreamHandler',
                      'stream': 'ext://sys.stderr',
                      'formatter': 'plain',
                      'level': 'WARNING'},
            'debug': {'class': 'logging.StreamHandler',
                      'stream': 'ext://sys.stderr',
                      'formatter': 'detail'},
        },
        # configure root logger:
        'root': {
            'handlers': ['debug' if opts['--verbose'] else 'error'],
            'level': level,
        },
    })

    try:
        steam = Steam(
            opts['--prefix'],
            opts['--root'],
            opts['--exe'],
            opts['--logfile'])
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1

    cli_mode = opts['store'] or opts['switch'] or opts['start']

    first, locked = steam.lock(['-foreground'])
    try:
        if not first:
            print("Acolyte is already running. Terminating.")
            return 0
        if cli_mode:
            if not locked:
                print("Waiting for steam to exit.")
                steam.wait_for_lock()
            if opts['store']:
                steam.store_login_cookie()
            elif opts['switch']:
                steam.switch_user(opts['<USER>'])
            elif opts['start']:
                steam.switch_user(opts['<USER>'])
                steam.unlock()
                steam.run().waitForFinished(-1)
                steam.lock()
                steam.store_login_cookie()
        else:
            from steam_acolyte.window import LoginDialog
            from steam_acolyte.theme import load_theme
            init_app()
            window = LoginDialog(steam, load_theme())
            window.show_trayicon()
            try:
                if locked:
                    steam.store_login_cookie()
                    window.show()
                else:
                    print("Waiting for steam to exit.")
                    window.show_waiting_message()
                    window.wait_for_lock()
                return app.exec_()
            finally:
                window.hide_trayicon()
    except KeyboardInterrupt:
        print()
        return 1
    finally:
        steam.unlock()
        steam.release_acolyte_instance_lock()


def init_app():
    import signal
    sys.excepthook = except_handler
    # Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt:
    # By default Ctrl-C has no effect in PyQt. For more information, see:
    # https://riverbankcomputing.com/pipermail/pyqt/2008-May/019242.html
    # https://docs.python.org/3/library/signal.html#execution-of-python-signal-handlers
    # http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-console
    signal.signal(signal.SIGINT, interrupt_handler)
    safe_timer(50, lambda: None)


def except_handler(*args, **kwargs):
    import traceback
    traceback.print_exception(*args, **kwargs)
    QApplication.quit()


def interrupt_handler(signum, frame):
    """Handle KeyboardInterrupt: quit application."""
    QApplication.quit()


def safe_timer(timeout, func, *args, **kwargs):
    """
    Create a timer that is safe against garbage collection and overlapping
    calls. See: http://ralsina.me/weblog/posts/BB974.html
    """
    def timer_event():
        try:
            func(*args, **kwargs)
        finally:
            QTimer.singleShot(timeout, timer_event)
    QTimer.singleShot(timeout, timer_event)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
