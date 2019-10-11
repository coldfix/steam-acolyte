CHANGES
-------

0.3.0
~~~~~

- learned to wait in the background for steam to exit when started after steam
- add single instance for acolyte to lock to guard against multiple acolyte
  instances waiting in the background at the same time
- more user friendly program exit upon Ctrl+C without showing a traceback
- add limited safeguards against exceptions due to missing keys in steam config
- remove --theme command line argument
- remove steam (original) theme
- remove scanning for steam in so far unencountered locations on linux


0.2.0
~~~~~

- add remove button that removes user from list
- engage in steam's single instance locking mechanism:

    - while running, block steam from being started
    - avoid actions while steam is running

  this prevents a common way of invalidating logins


0.1.1
~~~~~

- fix exception after closing steam


0.1.0
~~~~~

- fix incorrect steam path on ubuntu
- avoid storing config if obviously logged out
- refactor into package
- add version information to windows EXE
- add icon to windows EXE
- use our own acolyte icon theme


0.0.9
~~~~~

- fix broken EXE due to bug in pyinstaller with pyqt 5.12.3
- sort user list by user display name


0.0.8
~~~~~

- fix button appearing as standalone window for brief moment at startup
- fix the autodeployed .exe name to include the version tag


0.0.7
~~~~~

- fix backward incompatible syntax with py3.5
- automatic releases
- provide .exe


0.0.6
~~~~~

- support windows
- allow installing on python>=3.5


0.0.5
~~~~~

- hide "logout" button if action is not available
- update user list after steam exits
- fix mouseover highlighting not working after steam exits


0.0.4
~~~~~

- more modern dark theme
- show username along display name
- show tooltip with user ID
- steal some icons from steam application files
- add button for logging out
- add button to login with new account
- fix exception in except-handler ;)


0.0.3
~~~~~

- fix TypeError due to missing positional argument
- fix TypeError when started via the entry point
- read userinfo from loginusers.vdf


0.0.2
~~~~~

- fix not starting due to reassignment of __name__
- fix KeyError 'SteamID' when chosing user who was not logged in previously
- exit application on exception
