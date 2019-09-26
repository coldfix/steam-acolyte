from steam_acolyte.steam import SteamUser

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QFrame, QLabel, QAction, QStyle,
    QHBoxLayout, QVBoxLayout, QToolButton)

from importlib_resources import read_text

import os


def create_login_dialog(steam):
    window = QDialog()
    layout = QVBoxLayout()
    window.setLayout(layout)
    window.setWindowTitle("Steam Acolyte")
    users = steam.read_config('loginusers.vdf')['users']
    users = sorted(
        [SteamUser(steam_id,
                   user_info['AccountName'],
                   user_info['PersonaName'],
                   user_info['Timestamp'])
         for steam_id, user_info in users.items()],
        key=lambda u: (u.persona_name.lower(), u.account_name.lower()))
    for user in users:
        layout.addWidget(UserWidget(window, steam, user))
    layout.addWidget(
        UserWidget(window, steam, SteamUser('', '', '', '')))
    # steal window icon:
    steam_icon_path = os.path.join(steam.data, 'public', 'steam_tray.ico')
    if os.path.isfile(steam_icon_path):
        window.setWindowIcon(QIcon(steam_icon_path))
    window.setStyleSheet(read_text(__package__, 'window.css'))
    return window


class UserWidget(QFrame):

    def __init__(self, parent, steam, user):
        super().__init__(parent)
        self.steam = steam
        self.user = user
        layout = QHBoxLayout()
        labels = QVBoxLayout()

        ico_label = QLabel()
        if user.account_name:
            icon_path = os.path.join(
                steam.data, 'clientui', 'images', 'icons', 'nav_profile_idle.png')
        else:
            icon_path = os.path.join(
                steam.data, 'clientui', 'images', 'icons', 'nav_customize.png')
        if os.path.isfile(icon_path):
            ico_label.setPixmap(QIcon(icon_path).pixmap(QSize(128, 128)))
            ico_label.setToolTip(user.steam_id and
                                 "UID: {}".format(user.steam_id))

        top_label = QLabel(user.persona_name or "(other)")
        bot_label = QLabel(user.account_name or "New account")
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
        self.update_ui()

    def login_clicked(self):
        steam = self.steam
        steam.login_window.close()
        steam.login_window = None
        self.steam.switch_user(self.user.account_name)
        self.steam.run()
        self.steam.store_login_cookie()
        # Close and recreate after steam is finished. This serves two purposes:
        # 1. update user list and widget state
        # 2. fix ":hover" selector not working on linux after hide+show
        steam.login_window = create_login_dialog(steam)
        steam.login_window.show()

    def logout_clicked(self):
        self.steam.remove_login_cookie(self.user.account_name)
        self.update_ui()

    def mousePressEvent(self, event):
        self.login_clicked()

    def update_ui(self):
        enabled = self.steam.has_cookie(self.user.account_name)
        self.logout_button.setVisible(enabled)
        self.logout_action.setEnabled(enabled)

        if enabled:
            cross_icon_path = os.path.join(
                self.steam.data, 'clientui', 'images', 'icons', 'stop_loading.png')
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
