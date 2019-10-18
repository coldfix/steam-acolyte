from steam_acolyte.steam import SteamUser

from PyQt5.QtWidgets import (
    QDialog, QLabel, QToolButton, QAbstractButton,
    QAction, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QStyle, QStyleOption, QStylePainter)


def create_login_dialog(steam, theme):
    window = QDialog()
    layout = QVBoxLayout()
    window.setLayout(layout)
    window.setWindowTitle("Steam Acolyte")
    users = sorted(steam.users(), key=lambda u:
                   (u.persona_name.lower(), u.account_name.lower()))
    users.append(SteamUser('', '', '', ''))
    for user in users:
        layout.addWidget(UserWidget(theme, steam, user))
    window.setWindowIcon(theme.window_icon)
    window.setStyleSheet(theme.window_style)
    steam.command_received.connect(lambda *_: window.activateWindow())
    return window


class ButtonWidget(QAbstractButton):

    """Base class for custom composite button widgets."""

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        opt.state |= (QStyle.State_Sunken if self.isDown() else
                      QStyle.State_Raised)
        p = QStylePainter(self)
        p.drawPrimitive(QStyle.PE_Widget, opt)

    def sizeHint(self):
        return self.layout().totalSizeHint()


class UserWidget(ButtonWidget):

    def __init__(self, theme, steam, user):
        super().__init__()
        self.theme = theme
        self.steam = steam
        self.user = user

        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout = QHBoxLayout()
        labels = QVBoxLayout()

        ico_label = QLabel()
        icon = theme.user_icon if user.account_name else theme.plus_icon
        if icon:
            ico_label.setPixmap(icon)
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
        self.logout_action.setIcon(self.theme.logout_icon)
        self.logout_action.setToolTip("Delete saved login")
        self.delete_action = QAction()
        self.delete_action.triggered.connect(self.delete_clicked)
        self.delete_action.setIcon(theme.delete_icon)
        self.delete_action.setToolTip("Delete user from list")
        self.logout_button = QToolButton()
        self.logout_button.setDefaultAction(self.logout_action)
        self.delete_button = QToolButton()
        self.delete_button.setDefaultAction(self.delete_action)
        layout.setSpacing(0)
        layout.addWidget(ico_label)
        layout.addSpacing(10)
        layout.addLayout(labels)
        layout.addStretch()
        layout.addSpacing(10)
        layout.addWidget(self.logout_button)
        layout.addWidget(self.delete_button)
        self.setLayout(layout)
        self.clicked.connect(self.login_clicked)
        self.update_ui()

    def login_clicked(self):
        steam = self.steam
        steam.login_window.close()
        steam.login_window = None
        steam.switch_user(self.user.account_name)
        steam.run()
        steam.store_login_cookie()
        # Close and recreate after steam is finished. This serves two purposes:
        # 1. update user list and widget state
        # 2. fix ":hover" selector not working on linux after hide+show
        steam.login_window = create_login_dialog(steam, self.theme)
        steam.login_window.show()

    def logout_clicked(self):
        self.steam.remove_login_cookie(self.user.account_name)
        self.update_ui()

    def delete_clicked(self):
        self.steam.remove_user(self.user.account_name)
        self.hide()
        self.window().adjustSize()

    def update_ui(self):
        username = self.user.account_name
        self.logout_button.setVisible(self.steam.has_cookie(username))
        self.delete_button.setVisible(bool(username))
