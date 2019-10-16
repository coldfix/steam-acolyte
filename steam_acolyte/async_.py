from PyQt5.QtCore import QThread


class AsyncTask(QThread):

    """Read a file asynchronously. Emit signal whenever a new line becomes
    available."""

    def __init__(self, func):
        super().__init__()
        self.func = func

    def run(self):
        self.func()
