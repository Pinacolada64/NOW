# -*- coding: UTF-8 -*-
"""
Connection screen

Texts in this module will be shown to the user at login-time.

Evennia will look at global string variables (variables defined
at the "outermost" scope of this module and use it as the
connection screen. If there are more than one, Evennia will
randomize which one it displays.

The commands available to the user when the connection screen is shown
are defined in commands.default_cmdsets.UnloggedinCmdSet and the
screen is read and displayed by the unlogged-in "look" command.

"""

from django.conf import settings
from evennia import utils

CONNECTION_SCREEN = r"""
Welcome to the Novel Online World (NOW) 

========= a New Frontier in Text Based Online Gaming =========
 If you have an existing account, connect to it by typing:
      connect <username> <password>
 If you need to create an account, type (without the <>'s):
      create <username> <password>

    HELP for more info.     LOOK will re-show this screen.

   If you have spaces in your username,
        enclose your name in double quotes.
=============================================================="""
