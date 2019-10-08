import re
import shlex


def read_file(filename):
    """Read full contents of given file."""
    with open(filename) as f:
        return f.read()


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
        r'^(\w+)\s+(\w+)\((\w+\s*(?:,\s*\w+\s*)*)\)$', re.ASCII)
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
