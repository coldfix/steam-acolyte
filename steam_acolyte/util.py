def read_file(filename):
    """Read full contents of given file."""
    with open(filename) as f:
        return f.read()


def write_file(filename, text):
    """Write file with the given text."""
    with open(filename, 'wb') as f:
        f.write(text.encode('utf-8'))
