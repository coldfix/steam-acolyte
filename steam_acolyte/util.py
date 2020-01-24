import re
import shlex


def read_file(filename):
    """Read full contents of given file."""
    try:
        with open(filename) as f:
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


def func_lookup(lib, types, declarations):
    funcs = {}
    funcdecl = re.compile(
        r'^(\w+)\s+(\w+)\((\w+\s*(?:,\s*\w+\s*)*)?\)$', re.ASCII)
    for decl in declarations.split(';'):
        decl = decl.strip()
        if not decl:
            continue
        restype, name, argtypes = funcdecl.match(decl).groups()
        func = funcs[name] = getattr(lib, name)
        func.restype = getattr(types, restype)
        func.argtypes = [getattr(types, t.strip())
                         for t in argtypes.split(',')]
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
                d = ld[entry]
            else:
                d[entry] = {}
                d = d[entry]
    return d
