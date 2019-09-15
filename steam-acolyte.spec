# vim: ft=python

def get_version():
    import sys
    import os
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

    # The following is a hack specific to pyinstaller 3.5 that is needed to
    # pass a VSVersionInfo directly to EXE(): EXE assumes that the `version`
    # argument is a path-like object and therefore has to be tricked into
    # ignoring it by exhibiting a falsy value in boolean context. However, the
    # object is later passed into the `SetVersion` function which can also
    # handle VSVersionInfo directly.
    class VersionInfo(VSVersionInfo):
        _count = 0
        def __bool__(self):
            self._count += 1
            return self._count > 1

    return VersionInfo(
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
    datas=[
        ('steam_acolyte/*.css', 'steam_acolyte'),
    ]
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
    icon=None,
    version=get_version(),
)
