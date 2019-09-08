Steam Acolyte
=============

Lightweight account switcher/login keeper for steam.

This tool provides a simple UI to switch between different steam user accounts
without having to reenter your password/2FA. This works by copying the login
cookie (depot) for the last user to a temporary location and restoring this
config to the appropriate location when the particular user is selected from
the UI. There is no magic here, and we do not store any credentials
independently from steam!

This dictates a usage as follows:

- start ``acolyte``
- choose user
- enter password/2FA if required
- play games
- exit steam via "Exit" option
- do **not** use "Change Users!" from the steam menu (this will invalidate the
  login token)
- upon exiting steam, the current user cookie will be saved
- the user selection dialog will popup again
- choose user
- ...
