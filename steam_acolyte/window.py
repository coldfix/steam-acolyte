from steam_acolyte.steam import SteamUser
from steam_acolyte.async_ import AsyncTask
from steam_acolyte.util import Tracer

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QDialog, QLabel, QToolButton, QAbstractButton,
    QAction, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QStyle, QStyleOption, QStylePainter, QWidget,
    QSystemTrayIcon, QMenu, QApplication)


try:                        # PyQt >= 5.11
    QueuedConnection = Qt.ConnectionType.QueuedConnection
except AttributeError:      # PyQt < 5.11
    QueuedConnection = Qt.QueuedConnection


trace = Tracer(__name__)


class LoginDialog(QDialog):

    def __init__(self, steam, theme):
        super().__init__()
        self.steam = steam
        self.theme = theme
        self.trayicon = None
        self.wait_task = None
        self.process = None
        self._exit = False
        self._login = None
        self.user_widgets = []
        self.setLayout(QVBoxLayout())
        self.setWindowTitle("Steam Acolyte")
        self.setWindowIcon(theme.window_icon)
        self.setStyleSheet(theme.window_style)
        steam.command_received.connect(lambda *_: self.activateWindow())
        self.update_userlist()

    def update_userlist(self):
        """Update the user list widget from the config file."""
        self.clear_layout()
        users = sorted(self.steam.users(), key=lambda u:
                       (u.persona_name.lower(), u.account_name.lower()))
        users.append(SteamUser('', '', '', ''))
        for user in users:
            self.layout().addWidget(UserWidget(self, user))

    def clear_layout(self):
        """Remove all users from the user list widget."""
        # The safest way I found to clear a QLayout is to reparent it to a
        # temporary widget. This also recursively reparents, hides and later
        # destroys any child widgets.
        layout = self.layout()
        if layout is not None:
            dump = QWidget()
            dump.setLayout(layout)
            dump.deleteLater()
        self.setLayout(QVBoxLayout())

    @trace.method
    def wait_for_lock(self, *_):
        """Start waiting for the steam instance lock asynchronously, and
        show/activate the window when we acquire the lock."""
        if self._exit:
            self.close()
            return
        self.wait_task = AsyncTask(self.steam.wait_for_lock)
        self.wait_task.finished.connect(self._on_locked)
        self.wait_task.start()

    @trace.method
    def _on_locked(self):
        """Executed when steam instance lock is acquired. Executes any queued
        login command, or activates the user list widget if no command was
        queued."""
        if self._exit:
            self.close()
            return
        self.stopAction.setEnabled(False)
        self.wait_task = None
        self.steam.store_login_cookie()
        self.update_userlist()
        if self._login:
            self.run_steam(self._login)
            self._login = None
            return
        self.show()

    @trace.method
    def show_trayicon(self):
        """Create and show the tray icon."""
        self.trayicon = QSystemTrayIcon(self.theme.window_icon)
        self.trayicon.setVisible(True)
        self.trayicon.setToolTip(
            "acolyte - lightweight steam account manager")
        self.trayicon.activated.connect(self.trayicon_clicked)
        self.trayicon.setContextMenu(self.createMenu())

    @trace.method
    def hide_trayicon(self):
        """Hide and destroy the tray icon."""
        if self.trayicon is not None:
            self.trayicon.setVisible(False)
            self.trayicon.deleteLater()
            self.trayicon = None

    @trace.method
    def trayicon_clicked(self, reason):
        """Activate window when tray icon is left-clicked."""
        if reason == QSystemTrayIcon.Trigger:
            if self.steam.has_steam_lock():
                self.activateWindow()

    def createMenu(self):
        """Compose tray menu."""
        style = self.style()
        stop = self.stopAction = QAction('&Exit Steam', self)
        stop.setToolTip('Signal steam to exit.')
        stop.setIcon(style.standardIcon(QStyle.SP_MediaStop))
        stop.triggered.connect(self.exit_steam)
        stop.setEnabled(False)
        exit = QAction('&Quit', self)
        exit.setToolTip('Exit acolyte.')
        exit.setIcon(style.standardIcon(QStyle.SP_DialogCloseButton))
        exit.triggered.connect(self._on_exit)

        self.newUserAction = make_user_action(
            self, SteamUser('', '', '', ''))
        self.userActions = []
        menu = QMenu()
        menu.addSection('Login')
        menu.addAction(self.newUserAction)
        menu.addSeparator()
        menu.addAction(stop)
        menu.addAction(exit)
        menu.aboutToShow.connect(self.update_menu, QueuedConnection)
        return menu

    def update_menu(self):
        """Update menu just before showing: populate with current user list
        and set position from tray icon."""
        self.populate_menu()
        self.position_menu()

    def populate_menu(self):
        """Update user list menuitems in tray menu."""
        menu = self.trayicon.contextMenu()
        for action in self.userActions:
            menu.removeAction(action)
        users = sorted(self.steam.users(), key=lambda u:
                       (u.persona_name.lower(), u.account_name.lower()))
        self.userActions = [make_user_action(self, user) for user in users]
        menu.insertActions(self.newUserAction, self.userActions)

    def position_menu(self):
        """Set menu position from tray icon."""
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

    @trace.method
    def exit_steam(self):
        """Send shutdown command to steam."""
        self.stopAction.setEnabled(False)
        self.steam.stop()

    @trace.method
    def _on_exit(self, *_):
        """Exit acolyte."""
        # We can't quit if steam is still running because QProcess would
        # terminate the child with us. In this case, we hide the trayicon and
        # set an exit flag to remind us about to exit as soon as steam is
        # finished.
        self.hide_trayicon()
        if self.steam.has_steam_lock():
            self.close()
        else:
            self._exit = True
            self.steam.unlock()
            self.steam.release_acolyte_instance_lock()

    @trace.method
    def login(self, username):
        """
        Exit steam if open, and login the user with the given username.
        """
        if self.steam.has_steam_lock():
            self.run_steam(username)
        else:
            self._login = username
            self.exit_steam()

    @trace.method
    def run_steam(self, username):
        """Run steam as the given user."""
        # Close and recreate after steam is finished. This serves two purposes:
        # 1. update user list and widget state
        # 2. fix ":hover" selector not working on linux after hide+show
        self.hide()
        self.steam.switch_user(username)
        self.steam.unlock()
        self.stopAction.setEnabled(True)
        self.process = self.steam.run()
        self.process.finished.connect(self.wait_for_lock)

    @trace.method
    def show_waiting_message(self):
        """If we are in the background, show waiting message as balloon."""
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


def make_user_action(window, user):
    """Create a QAction for logging in the given user."""
    theme = window.theme
    action = QAction(user.persona_name or "(New account)", window)
    action.triggered.connect(lambda: window.login(user.account_name))
    action.setToolTip("Login {}".format(
        user.account_name or "new account"))
    action.setIcon(QIcon(
        theme.user_icon if user.account_name else theme.plus_icon))
    return action


class UserWidget(ButtonWidget):

    """A button widget for a single user. When clicked, logs in that user.
    Contains small buttons that delete the login token and remove the user
    from the list."""

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
        self.window().login(self.user.account_name)

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
