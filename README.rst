Steam Acolyte
=============

Steam account switcher - lightweight program to switch between steam accounts
without having to reenter password/2FA.

|Screenshot|

- works on **windows** and **linux**
- one click to login the corresponding user
- works on the first start using your existing login
- waits in the background while steam is running
- close steam and directly login another user via the tray menu
- automatically shows a list of users previously logged in on this machine
  by reading steam config files
- has buttons to delete saved logins and/or remove users from the list
- never comes in contact with any of your passwords
- includes a simple command line interface


Installation
------------

Install the latest version from PyPI::

    pip install --user steam-acolyte

**Alternatively**, if you want this application to live independently from other python packages,
I recommend using pipx_ rather than *pip*::

    pip install --user pipx
    pipx install steam-acolyte

.. _pipx: https://pipxproject.github.io/pipx/

**For windows**, an all-inclusive ``.exe`` file can be created using
PyInstaller_ from the development files as follows::

    pip install -U pyinstaller
    pyinstaller steam-acolyte.spec

This ``.exe`` can also be downloaded from the `github releases`_ page. Expect
that on the first execution windows shows a warning dialog along the lines of
"Windows Defender SmartScreen prevented an unrecognized app from starting.
Running this app might put your PC at risk". Click "More info" and then "Run
anyway" to acknowledge the warning. This is normal because I didn't buy a code
signing certificate.

.. _pyinstaller: http://www.pyinstaller.org/
.. _github releases: https://github.com/coldfix/steam-acolyte/releases


Usage
-----

Simply run ``steam-acolyte`` instead of ``steam``.

In order to switch users, exit steam via the "Exit" option, or use acolyte's
tray menu.

Optionally, modify your steam launchers to execute ``steam-acolyte``.


How it works
------------

*acolyte* works dead-simple by saving the login token for the last active
steam account upon program start. When the user clicks on a particular account
it simply restores the corresponding token and then starts steam. *acolyte*
only stores login tokes, but never any passwords! This has the following
implications:

- the login token can be used to login without having to re-enter 2FA
  (whereas for password-based logins you would need to redo 2FA)
- the login token can only be used for a single login
- after a successful login, steam will create a fresh token which acolyte can
  save for the next cycle when steam exits or when acolyte is started the next
  time
- it is no problem to start and exit steam several times without acolyte
  running (as long as you always sign on with the same account), because
  acolyte will always pick up the most recent login token when it starts
- the token expires if unused for a several weeks
- selecting "Change Account" from the steam menu or "Log Out User" in Big
  Picture mode UI invalidates the login and you will have to reenter your
  password for the logged out user


.. |Screenshot| image:: https://raw.githubusercontent.com/coldfix/steam-acolyte/master/screenshot.png
   :target:             https://raw.githubusercontent.com/coldfix/steam-acolyte/master/screenshot.png
   :alt:                Screenshot (usernames were changed)
