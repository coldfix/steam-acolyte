from setuptools import setup


meta = {}
with open('steam_acolyte.py', 'rb') as f:
    try:
        exec(f.read(), meta, meta)
    except ImportError:     # ignore missing dependencies at setup time
        pass                # and return dunder-globals anyway!

setup(
    name    = meta['__name__'],
    version = meta['__version__'],
    url     = meta['__url__'],
)
