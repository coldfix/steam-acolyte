# vim: ft=python

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
)
