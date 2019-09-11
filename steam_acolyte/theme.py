
from PyQt5.QtGui import QIcon

from importlib_resources import read_text

import os
from types import SimpleNamespace


def steam_theme(steam):
    return SimpleNamespace(
        window_style = read_text('steam_acolyte', 'window.css'),
        window_icon = load_icon_file(os.path.join(
            steam.data, 'public', 'steam_tray.ico')),
        delete_icon = load_icon_file(os.path.join(
            steam.data, 'clientui', 'images', 'icons',
            'stop_loading.png')),
        user_icon = load_icon_file(os.path.join(
            steam.data, 'clientui', 'images', 'icons',
            'nav_profile_idle.png'), 32, 32),
        plus_icon = load_icon_file(os.path.join(
            steam.data, 'clientui', 'images', 'icons',
            'nav_customize.png'), 32, 32),
    )


THEMES = {
    'default': steam_theme,
    'steam': steam_theme,
}


def load_theme(steam, theme_name):
    theme_name = theme_name or 'default'
    if theme_name not in THEMES:
        print('Warning: unknown theme {!r}'.format(theme_name))
        theme_name = 'default'
    return THEMES[theme_name](steam)


def load_icon_file(filename, *size):
    if os.path.isfile(filename):
        icon = QIcon(filename)
        return icon.pixmap(*size) if size else icon
