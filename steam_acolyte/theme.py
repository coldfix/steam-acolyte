from PyQt5.QtGui import QIcon

try:
    from importlib.resources import read_text, path
except ImportError:
    from importlib_resources import read_text, path

import os
from types import SimpleNamespace


def load_theme():
    return SimpleNamespace(
        window_style = read_text(__package__, 'window.css'),
        window_icon = load_icon_resource('acolyte.svg'),
        logout_icon = load_icon_resource('logout.svg'),
        delete_icon = load_icon_resource('delete.svg'),
        user_icon = load_icon_resource('user.svg', 32, 32),
        plus_icon = load_icon_resource('plus.svg', 32, 32),
    )


def load_icon_file(filename, *size):
    if os.path.isfile(filename):
        icon = QIcon(filename)
        return icon.pixmap(*size) if size else icon


def load_icon_resource(name, *size):
    with path(__package__, name) as p:
        return load_icon_file(str(p), *size)
