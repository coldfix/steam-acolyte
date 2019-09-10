CHANGES
-------

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
