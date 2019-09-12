from setuptools import setup


meta = {}
with open('steam_acolyte/__init__.py', 'rb') as f:
    try:
        exec(f.read(), meta, meta)
    except ImportError:     # ignore missing dependencies at setup time
        pass                # and return dunder-globals anyway!

setup(
    name    = meta['__title__'],
    version = meta['__version__'],
    url     = meta['__url__'],
)
