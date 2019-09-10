#! /usr/bin/env python
"""
A lightweight steam account manager and switcher.

Usage:
    steam-acolyte [options]
    steam-acolyte [options] store
    steam-acolyte [options] switch <USER>
    steam-acolyte [options] start <USER>

Options:
    -r ROOT, --root ROOT        Steam root path
"""

__title__   = "steam-acolyte"
__version__ = "0.0.3"
__url__     = "https://github.com/coldfix/steam-acolyte"

import vdf
from docopt import docopt

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication, QDialog, QWidget,
    QHBoxLayout, QVBoxLayout, QPushButton)

import os
import sys
from shutil import copyfile
from functools import partial


STEAM_ROOT_PATH = [
    '~/.local/share/Steam',
    '~/.steam/root',
    '~/.steam',
]


def main(args=None):
    opts = docopt(__doc__, args)
    root = opts['--root'] or find_steam_root()
    if root is None:
        print("""Unable to find steam user path!""", file=sys.stderr)
        return 1
    if opts['store']:
        store_login_cookie(root)
    elif opts['switch']:
        switch_user(root, opts['<USER>'])
    elif opts['start']:
        switch_user(root, opts['<USER>'])
        run_steam()
        store_login_cookie(root)
    else:
        run_gui(root)


def run_gui(root):
    import signal
    app = QApplication([])
    sys.excepthook = except_handler
    # Setup handling of KeyboardInterrupt (Ctrl-C) for PyQt:
    # By default Ctrl-C has no effect in PyQt. For more information, see:
    # https://riverbankcomputing.com/pipermail/pyqt/2008-May/019242.html
    # https://docs.python.org/3/library/signal.html#execution-of-python-signal-handlers
    # http://stackoverflow.com/questions/4938723/what-is-the-correct-way-to-make-my-pyqt-application-quit-when-killed-from-the-console
    signal.signal(signal.SIGINT, interrupt_handler)
    safe_timer(50, lambda: None)
    window = create_login_dialog(root)
    window.show()
    return app.exec_()


def create_login_dialog(root):
    window = QDialog()
    layout = QVBoxLayout()
    window.setLayout(layout)
    window.setWindowTitle("Steam Acolyte")
    users = read_steam_config(root, 'loginusers.vdf')['users']
    for userinfo in users.values():
        username = userinfo['AccountName']
        button = create_login_button(root, window, username)
        layout.addWidget(button)
    return window


def create_login_button(root, window, username):
    widget = QWidget()
    layout = QHBoxLayout()
    button = QPushButton(username)
    button.clicked.connect(partial(
        user_button_clicked, window, root, username))
    layout.addWidget(button)
    widget.setLayout(layout)
    return widget


def user_button_clicked(window, root, username):
    window.hide()
    switch_user(root, username)
    run_steam()
    store_login_cookie(root)
    window.show()


def store_login_cookie(root):
    username = get_last_user(root)
    userpath = os.path.join(root, 'acolyte', username, 'config.vdf')
    configpath = os.path.join(root, 'config', 'config.vdf')
    os.makedirs(os.path.dirname(userpath), exist_ok=True)
    copyfile(configpath, userpath)


def switch_user(root, username):
    """Switch login config to given user. Do not use this while steam is
    running."""
    set_last_user(root, username)
    userpath = os.path.join(root, 'acolyte', username, 'config.vdf')
    configpath = os.path.join(root, 'config', 'config.vdf')
    if not os.path.isfile(userpath):
        print(f"No stored config found for {username!r}", file=sys.stderr)
        return False
    copyfile(userpath, configpath)
    return True


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


def read_steam_config(root, filename='config.vdf'):
    """Read steam config.vdf file."""
    conf = os.path.join(root, 'config', filename)
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


def except_handler():
    import traceback
    traceback.print_exception()
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
