CHANGES
-------

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
