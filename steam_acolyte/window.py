from steam_acolyte.steam import SteamUser
from steam_acolyte.async_ import AsyncTask

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QLabel, QToolButton, QAbstractButton,
    QAction, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QStyle, QStyleOption, QStylePainter, QWidget,
    QSystemTrayIcon, QMenu, QApplication)


try:                        # PyQt >= 5.11
    QueuedConnection = Qt.ConnectionType.QueuedConnection
except AttributeError:      # PyQt < 5.11
    QueuedConnection = Qt.QueuedConnection


class LoginDialog(QDialog):

    def __init__(self, steam, theme):
        super().__init__()
        self.steam = steam
        self.theme = theme
        self.trayicon = None
        self.wait_task = None
        self.process = None
        self._exit = False
        self.user_widgets = []
        self.setLayout(QVBoxLayout())
        self.setWindowTitle("Steam Acolyte")
        self.setWindowIcon(theme.window_icon)
        self.setStyleSheet(theme.window_style)
        steam.command_received.connect(lambda *_: self.activateWindow())
        self.update_userlist()

    def update_userlist(self):
        self.clear_layout()
        users = sorted(self.steam.users(), key=lambda u:
                       (u.persona_name.lower(), u.account_name.lower()))
        users.append(SteamUser('', '', '', ''))
        for user in users:
            self.layout().addWidget(UserWidget(self, user))

    def clear_layout(self):
        # The safest way I found to clear a QLayout is to reparent it to a
        # temporary widget. This also recursively reparents, hides and later
        # destroys any child widgets.
        layout = self.layout()
        if layout is not None:
            dump = QWidget()
            dump.setLayout(layout)
            dump.deleteLater()
        self.setLayout(QVBoxLayout())

    def wait_for_lock(self):
        if self._exit:
            self.close()
            return
        self.wait_task = AsyncTask(self.steam.wait_for_lock)
        self.wait_task.finished.connect(self._on_locked)
        self.wait_task.start()

    def _on_locked(self):
        if self._exit:
            self.close()
            return
        self.wait_task = None
        self.steam.store_login_cookie()
        self.update_userlist()
        self.show()

    def show_trayicon(self):
        self.trayicon = QSystemTrayIcon(self.theme.window_icon)
        self.trayicon.setVisible(True)
        self.trayicon.setToolTip(
            "acolyte - lightweight steam account manager")
        self.trayicon.activated.connect(self.trayicon_clicked)
        self.trayicon.setContextMenu(self.createMenu())

    def hide_trayicon(self):
        if self.trayicon is not None:
            self.trayicon.setVisible(False)
            self.trayicon.deleteLater()
            self.trayicon = None

    def trayicon_clicked(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.activateWindow()

    def createMenu(self):
        style = self.style()
        exit = QAction('&Quit', self)
        exit.setToolTip('Exit acolyte.')
        exit.setIcon(style.standardIcon(QStyle.SP_DialogCloseButton))
        exit.triggered.connect(self._on_exit)
        menu = QMenu()
        menu.addAction(exit)
        menu.aboutToShow.connect(self.position_menu, QueuedConnection)
        return menu

    def position_menu(self):
        menu = self.trayicon.contextMenu()
        desktop = QApplication.desktop()
        screen = QApplication.screens()[desktop.screenNumber(menu)]

        screen_geom = screen.availableGeometry()
        menu_size = menu.sizeHint()
        icon_geom = self.trayicon.geometry()

        if icon_geom.left() + menu_size.width() <= screen_geom.right():
            left = icon_geom.left()
        elif icon_geom.right() - menu_size.width() >= screen_geom.left():
            left = icon_geom.right() - menu_size.width()
        else:
            return

        if icon_geom.bottom() + menu_size.height() <= screen_geom.bottom():
            top = icon_geom.bottom()
        elif icon_geom.top() - menu_size.height() >= screen_geom.top():
            top = icon_geom.top() - menu_size.height()
        else:
            return

        menu.move(left, top)

    def _on_exit(self):
        """Exit acolyte."""
        # We can't quit if steam is still running because QProcess would
        # terminate the child with us. In this case, we hide the trayicon and
        # set an exit flag that to remind us about to exit as soon as steam is
        # finished.
        self.hide_trayicon()
        if self.isVisible():
            self.close()
        else:
            self._exit = True
            self.steam.unlock()
            self.steam.release_acolyte_instance_lock()

    def run_steam(self, username):
        # Close and recreate after steam is finished. This serves two purposes:
        # 1. update user list and widget state
        # 2. fix ":hover" selector not working on linux after hide+show
        self.hide()
        self.steam.switch_user(username)
        self.steam.unlock()
        self.process = self.steam.run()
        self.process.finished.connect(self.wait_for_lock)

    def show_waiting_message(self):
        if self.trayicon is not None:
            self.trayicon.showMessage(
                "steam-acolyte", "The damned stand ready.")


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

    def __init__(self, window, user):
        super().__init__(window)
        self.steam = window.steam
        self.theme = window.theme
        self.user = user

        self.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout = QHBoxLayout()
        labels = QVBoxLayout()

        theme = self.theme
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
        self.window().run_steam(self.user.account_name)

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
