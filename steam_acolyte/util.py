import re
import shlex
import logging
from steam_acolyte.funcwrap import wraps


def read_file(filename):
    """Read full contents of given file."""
    try:
        with open(filename, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def write_file(filename, text):
    """Write file with the given text."""
    with open(filename, 'wb') as f:
        f.write(text.encode('utf-8'))


def join_args(args):
    """Compose command line from argument list."""
    return ' '.join(map(shlex.quote, args))


def import_declarations(lib, types, declarations):
    """Lookup C declarations from the given ctypes library object."""
    funcs = {}
    funcdecl = re.compile(
        r'^(\w+)\s+(\w+)\((\w+\s*(?:,\s*\w+\s*)*)?\)$', re.ASCII)
    for line in declarations.split(';'):
        line = line.strip()
        if line:
            restype, name, argtypes = funcdecl.match(line).groups()
            func = funcs[name] = getattr(lib, name)
            func.restype = getattr(types, restype)
            func.argtypes = [
                getattr(types, t.strip())
                for t in argtypes.split(',')
            ]
    return funcs


def subkey_lookup(d, path):
    """Case-insensitive dictionary lookup that autovivifies non-existing
    entries. `path` is a '\\' separated string.

    Reasons to use this function to lookup entries in steam config:

    - because I sometimes found lowercase keys in the `config.vdf` file
    - for for some protection against exceptions due to missing keys
    - more similar syntax compared to the windows registry lookup
    - more concise syntax
    """
    for entry in path.split('\\'):
        if entry in d:
            d = d[entry]
        else:
            ld = {k.lower(): v for k, v in d.items()}
            if entry.lower() in ld:
                d = ld[entry.lower()]
            else:
                d[entry] = {}
                d = d[entry]
    return d


class Tracer:

    def __init__(self, name):
        self.name = name

    def __call__(self, *args, **kwargs):
        logging.getLogger(self.name).debug(*args, **kwargs)

    def method(self, fn):
        """Trace a method call."""
        def wrapper(*args, **kwargs):
            obj, args = args[0], args[1:]
            self('%s.%s(%s)',
                 obj.__class__.__name__,
                 fn.__name__,
                 format_callargs(*args, **kwargs))
            return fn(obj, *args, **kwargs)
        # Use `wrap` to preserve the signature exactly on the python syntax
        # level. This is required to make pyqtsignal dispatch the same signal
        # signature:
        return wraps(fn, wrapper)


def format_callargs(*args, **kwargs):
    allargs = [short_repr(arg) for arg in args]
    allargs += ['{}={}'.format(k, short_repr(v)) for k, v in kwargs.items()]
    return ', '.join(allargs)


def short_repr(val):
    s = repr(val)
    if len(s) > 30:
        s = s[:5] + ' ... ' + s[:-5]
    return s
