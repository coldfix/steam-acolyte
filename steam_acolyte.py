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
__version__ = "0.0.8"
__url__     = "https://github.com/coldfix/steam-acolyte"

import vdf
from docopt import docopt

from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFrame, QLabel, QAction, QStyle,
    QHBoxLayout, QVBoxLayout, QToolButton)

import os
import sys
from shutil import copyfile


def main(args=None):
    opts = docopt(__doc__, args)
    try:
        steam = Steam(opts['--root'])
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1

    if opts['store']:
        steam.store_login_cookie()
    elif opts['switch']:
        steam.switch_user(opts['<USER>'])
    elif opts['start']:
        steam.switch_user(opts['<USER>'])
        steam.run()
        steam.store_login_cookie()
    else:
        run_gui(steam)


def run_gui(steam):
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
    steam.login_window = create_login_dialog(steam)
    steam.login_window.show()
    return app.exec_()


def create_login_dialog(steam):
    window = QDialog()
    layout = QVBoxLayout()
    window.setLayout(layout)
    window.setWindowTitle("Steam Acolyte")
    users = steam.read_config('loginusers.vdf')['users']
    for steam_id, userinfo in users.items():
        persona_name = userinfo['PersonaName']
        account_name = userinfo['AccountName']
        layout.addWidget(
            UserWidget(window, steam, persona_name, account_name,
                       "UID: {}".format(steam_id)))
    layout.addWidget(
        UserWidget(window, steam, "(other)", ""))
    # steal window icon:
    steam_icon_path = os.path.join(steam.root, 'public', 'steam_tray.ico')
    if os.path.isfile(steam_icon_path):
        window.setWindowIcon(QIcon(steam_icon_path))
    window.setStyleSheet("""
QDialog {
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 #1B2137,
        stop: 1 #2A2E33
    );
    color: #DDDDDD;
}
    """)
    return window


class UserWidget(QFrame):

    def __init__(self, parent, steam, persona_name, account_name, steam_id=""):
        super().__init__(parent)
        self.steam = steam
        self.user = account_name
        layout = QHBoxLayout()
        labels = QVBoxLayout()

        ico_label = QLabel()
        if account_name:
            icon_path = os.path.join(
                steam.root, 'clientui', 'images', 'icons', 'nav_profile_idle.png')
        else:
            icon_path = os.path.join(
                steam.root, 'clientui', 'images', 'icons', 'nav_customize.png')
        if os.path.isfile(icon_path):
            ico_label.setPixmap(QIcon(icon_path).pixmap(QSize(128, 128)))
            ico_label.setToolTip(steam_id)

        top_label = QLabel(persona_name)
        bot_label = QLabel(account_name or "New account")
        top_label.setObjectName("PersonaName")
        bot_label.setObjectName("AccountName")
        top_font = top_label.font()
        top_font.setBold(True)
        top_font.setPointSize(top_font.pointSize() + 2)
        top_label.setFont(top_font)
        labels.addWidget(top_label)
        labels.addWidget(bot_label)
        self.logout_action = QAction()
        self.logout_action.triggered.connect(self.logout_clicked)
        self.logout_button = QToolButton()
        self.logout_button.setDefaultAction(self.logout_action)
        layout.addWidget(ico_label)
        layout.addSpacing(10)
        layout.addLayout(labels)
        layout.addStretch()
        layout.addSpacing(10)
        layout.addWidget(self.logout_button)
        self.setLayout(layout)
        self.setFrameShape(QFrame.Box)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
QFrame {
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 1 #383E46,
        stop: 0 #4A4E53
    );

    border-style: solid;
    border-width: 1px;
    border-radius: 10px;
    border-color: #AAAAAA;
    color: #DDDDDD;
}

QFrame:hover {
    background: qlineargradient(
        x1: 0, y1: 0,
        x2: 0, y2: 1,
        stop: 0 #585E66,
        stop: 1 #6A6E73
    );
}

QLabel#PersonaName {
    color: white;
}

QLabel {
    background: transparent;
    border: none;
}
QLabel:hover {
    background: transparent;
    border: none;
}

QToolButton {
    border: none;
    padding: 3px;
}
QToolButton:hover {
    border-style: solid;
    border-width: 1px;
    border-radius: 5px;
    border-color: #5A5E63;
    background: #565460;
}
        """)
        self.update_ui()

    def login_clicked(self):
        steam = self.steam
        steam.login_window.close()
        steam.login_window = None
        self.steam.switch_user(self.user)
        self.steam.run()
        self.steam.store_login_cookie()
        # Close and recreate after steam is finished. This serves two purposes:
        # 1. update user list and widget state
        # 2. fix ":hover" selector not working on linux after hide+show
        steam.login_window = create_login_dialog(steam)
        steam.login_window.show()

    def logout_clicked(self):
        self.steam.remove_login_cookie(self.user)
        self.update_ui()

    def mousePressEvent(self, event):
        self.login_clicked()

    def update_ui(self):
        enabled = self.steam.has_cookie(self.user)
        self.logout_button.setVisible(enabled)
        self.logout_action.setEnabled(enabled)

        if enabled:
            cross_icon_path = os.path.join(
                self.steam.root, 'clientui', 'images', 'icons', 'stop_loading.png')
            if os.path.isfile(cross_icon_path):
                cross_icon = QIcon(cross_icon_path)
            else:
                cross_icon = self.style().standardIcon(
                    QStyle.SP_DialogCancelButton)
            self.logout_action.setIcon(cross_icon)

        if enabled:
            self.logout_action.setToolTip("Delete saved login")
        else:
            self.logout_action.setToolTip("")


class Steam:

    STEAM_ROOT_PATH = [
        '~/.local/share/Steam',
        '~/.steam/root',
        '~/.steam',
    ]

    def __init__(self, root=None, exe=None):
        self.root = root or self.find_root()
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
        """Locate and return the root path for the steam program files and user
        configuration."""
        if sys.platform == 'win32':
            return read_steam_registry_value("SteamPath")
        else:
            for root in cls.STEAM_ROOT_PATH:
                root = os.path.expanduser(root)
                conf = os.path.join(root, 'config', 'config.vdf')
                if os.path.isdir(root) and os.path.isfile(conf):
                    return root
        raise RuntimeError("""Unable to find steam user path!""")

    @classmethod
    def find_exe(cls):
        if sys.platform == 'win32':
            return read_steam_registry_value("SteamExe")
        else:
            return 'steam'


def read_file(filename):
    """Read full contents of given file."""
    with open(filename) as f:
        return f.read()


def read_steam_registry_value(value_name):
    import winreg
    with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
        return winreg.QueryValueEx(key, value_name)[0]


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
