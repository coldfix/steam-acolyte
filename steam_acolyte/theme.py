
from PyQt5.QtGui import QIcon

from importlib_resources import read_text, path

import os
from types import SimpleNamespace


def builtin_theme(steam):
    return SimpleNamespace(
        window_style = read_text(__package__, 'window.css'),
        window_icon = load_icon_resource('acolyte.svg'),
        logout_icon = load_icon_resource('logout.svg'),
        delete_icon = load_icon_resource('delete.svg'),
        user_icon = load_icon_resource('user.svg', 32, 32),
        plus_icon = load_icon_resource('plus.svg', 32, 32),
    )


def steam_theme(steam):
    return SimpleNamespace(
        window_style = read_text('steam_acolyte', 'window.css'),
        window_icon = load_icon_file(os.path.join(
            steam.data, 'public', 'steam_tray.ico')),
        logout_icon = load_icon_file(os.path.join(
            steam.data, 'clientui', 'images', 'icons',
            'left.png')),
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
    'default': builtin_theme,
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


def load_icon_resource(name, *size):
    with path(__package__, name) as p:
        return load_icon_file(str(p), *size)
