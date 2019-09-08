Steam Acolyte
=============

Lightweight user account switcher/login keeper for steam.

This tool provides a simple UI to switch between different steam user accounts
without having to reenter your password/2FA. This works by copying the
credentials depot which contains a login token for the last active user to a
temporary location. This config is restored to the appropriate location when
the particular user is selected from the UI.

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

There is no magic interaction with steam here, and we do not store any
credentials independently from steam!

Note that only linux is supported currently. Windows support is planned.
