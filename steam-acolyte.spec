# vim: ft=python
from PyInstaller.utils.hooks import collect_data_files

import sys
import os


def get_version():
    if sys.platform != 'win32':
        return None
    from PyInstaller.utils.win32.versioninfo import (
        VSVersionInfo, FixedFileInfo, StringFileInfo,
        StringTable, StringStruct, VarFileInfo, VarStruct)
    meta = {}
    with open('steam_acolyte/__init__.py', 'rb') as f:
        try:
            exec(f.read(), meta, meta)
        except ImportError:     # ignore missing dependencies at setup time
            pass                # and return dunder-globals anyway!

    ver_str = meta['__version__']
    version = ver_str.split('.')
    version = [int(p) for p in version if p.isnumeric()]
    version += [int(os.environ.get('APPVEYOR_BUILD_NUMBER', 0))]

    return VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=tuple(version)[:4],
            prodvers=tuple(version)[:4],
        ),
        kids=[
            StringFileInfo([
                StringTable('040904E4', [
                    StringStruct('CompanyName', 'Thomas Gläßle'),
                    StringStruct('FileDescription', 'Steam Login Manager'),
                    StringStruct('FileVersion', ver_str),
                    StringStruct('InternalName', 'steam-acolyte'),
                    StringStruct('LegalCopyright', '© Thomas Gläßle. All rights reserved.'),
                    StringStruct('OriginalFilename', 'steam-acolyte.exe'),
                    StringStruct('ProductName', 'Steam Acolyte'),
                    StringStruct('ProductVersion', ver_str),
                ])
            ]),
            VarFileInfo([VarStruct(u'Translation', [0x409, 1252])])
        ]
    )


a = Analysis(
    ['steam_acolyte/__main__.py'],
    pathex=['.'],
    datas=(
        collect_data_files('steam_acolyte') +
        (collect_data_files('importlib_resources')
         if sys.version_info < (3, 7) else []))
)

pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='steam-acolyte',
    console=False,
    icon='acolyte.ico' if os.path.isfile('acolyte.ico') else None,
    version=get_version(),
)
