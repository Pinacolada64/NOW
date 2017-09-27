"""
Evennia settings file.

The available options are found in the default settings file found
here:

/home/NOW/NOWMU/evennia/evennia/settings_default.py

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

SERVERNAME = "NOW"

TELNET_PORTS = [4000, 8888]

WEBSERVER_PORTS = [(8000, 8001)]

IDMAPPER_CACHE_MAXSIZE = 150

INLINEFUNC_ENABLED = False  # Too buggy to use, currently.

IDLE_TIMEOUT = 5 * 60 * 60  # 5 hours

MULTISESSION_MODE = 1

IRC_ENABLED = True  # @irc2chan Public = irc.furnet.org 7000 #NOW NOW

IN_GAME_ERRORS = False  # Errors in console are sufficient.

SEARCH_MULTIMATCH_REGEX = r"(?P<number>[0-9]+) (?P<name>.*)"
SEARCH_MULTIMATCH_TEMPLATE = " {number} {name}{aliases}{info}\n"

ENCODINGS = ["utf-8", "latin-1", "ISO-8859-1", "cp437"]

######################################################################
# Player settings
######################################################################

HELP_MORE = False
PERMISSION_HIERARCHY = ["Guest",  # NOTE: only used if GUEST_ENABLED=True
                        "Denizen",
                        "Citizen",
                        "Helper",
                        "Crafter",
                        "Builder",
                        "Helpstaff",
                        "Mage",
                        "Wizard",
                        "Immortal"]
