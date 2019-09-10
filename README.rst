Steam Acolyte
=============

Lightweight user account switcher/login keeper for steam.

This tool provides a simple UI to switch between different steam user accounts
without having to reenter your password/2FA. This works by copying the
credentials depot which contains a login token for the last active user to a
temporary location. This config is restored to the appropriate location when
the particular user is selected from the UI.

|Screenshot|

There is no magic interaction with steam here, and we do not store any
credentials independently from steam!

Note that only linux is supported currently. Windows support is planned.


Installation
------------

Install the latest version from PyPI::

    pip install --user steam-acolyte

If you want this application to live independently from other python packages,
I recommend using pipx_ rather than *pip*.

.. _pipx: https://pipxproject.github.io/pipx/


Usage
-----

Simply launch ``steam-acolyte`` instead of ``steam``.

In order to switch users, exit steam via the "Exit" option. In particular do
**not** use the "Change Account..." option from the steam menu (this will
invalidate the login token)!

It is adviceable not to mix launching steam via acolyte or regularly (this
might result in your active logins being invalidated), and I therefore
recommend modifying your steam launcher to execute ``steam-acolyte``.


.. |Screenshot| image:: https://raw.githubusercontent.com/coldfix/steam-acolyte/master/screenshot.png
   :target:             https://raw.githubusercontent.com/coldfix/steam-acolyte/master/screenshot.png
   :alt:                Screenshot (usernames were changed)
