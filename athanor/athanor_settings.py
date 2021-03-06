r"""
Athanor settings file.

The available options are found in the default settings file found
here:

evennia/settings_default.py

Remember:

This is for settings that Athanor assumes. For your own server's
settings, adjust <mygame>/server/conf/settings.py. See the instructions there for more
information.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *
from collections import defaultdict
import athanor, sys

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!
SERVERNAME = "Athanor: Advent of Awesome"

# Server ports. If enabled and marked as "visible", the port
# should be visible to the outside world on a production server.
# Note that there are many more options available beyond these.

# Telnet ports. Visible.
TELNET_ENABLED = True
TELNET_PORTS = [4000]
# (proxy, internal). Only proxy should be visible.
WEBSERVER_ENABLED = True
WEBSERVER_PORTS = [(4001, 4002)]
# Telnet+SSL ports, for supporting clients. Visible.
SSL_ENABLED = False
SSL_PORTS = [4003]
# SSH client ports. Requires crypto lib. Visible.
SSH_ENABLED = False
SSH_PORTS = [4004]
# Websocket-client port. Visible.
WEBSOCKET_CLIENT_ENABLED = True
WEBSOCKET_CLIENT_PORT = 4005
# Internal Server-Portal port. Not visible.
AMP_PORT = 4006

# Of course we want these on!
IRC_ENABLED = True
RSS_ENABLED = True

# Let's disable that annoying timeout by default!
IDLE_TIMEOUT = -1

# A lot of MUD-styles may want to change this to 2. Athanor's not really meant for 0 or 1 style, though.
MULTISESSION_MODE = 3

USE_TZ = True
TELNET_OOB_ENABLED = True
WEBSOCKET_ENABLED = True
INLINEFUNC_ENABLED = True

AT_INITIAL_SETUP_HOOK_MODULE = "athanor.at_initial_setup"
AT_SERVER_STARTSTOP_MODULE = "athanor.at_server_startstop"

HELP_MORE = False

CONNECTION_SCREEN_MODULE = "athanor.connection_screens"

CMD_IGNORE_PREFIXES = ""

# The Styler is an object that generates commonly-used formatting, like
# headers and tables.
STYLER_CLASS = "athanor.utils.styling.Styler"

# The EXAMINE HOOKS are used to generate Examine-styled output. It differs by types.
EXAMINE_HOOKS = defaultdict(list)

EXAMINE_HOOKS['object'] = ['object', 'puppeteer', 'access', 'commands', 'scripts', 'tags', 'attributes', 'contents']

######################################################################
# Controllers
######################################################################
CONTROLLER_MANAGER_CLASS = "athanor.controllers.base.ControllerManager"
BASE_CONTROLLER_CLASS = "athanor.controlers.base.AthanorController"

CONTROLLERS = dict()


######################################################################
# Game Data System
######################################################################
CONTROLLERS['gamedata'] = {
    'class': 'athanor.controllers.gamedata.AthanorGameDataController',
}


######################################################################
# Session Options
######################################################################
# Command set used on the logged-in session
CMDSET_SESSION = "athanor.cmdsets.session.AthanorSessionCmdSet"

# Command set used on session before account has logged in
CMDSET_UNLOGGEDIN = "athanor.cmdsets.login.AthanorUnloggedinCmdSet"

SERVER_SESSION_CLASS = "athanor.gamedb.sessions.AthanorSession"

EXAMINE_HOOKS['session'] = []

######################################################################
# Plugin Options
######################################################################


# KINDS CLASSES
DEFAULT_ENTITY_CLASSES = {
    'areas': "athanor.entities.areas.AthanorArea",
    'exits': "athanor.entities.exits.AthanorExit",
    "gateway": "athanor.entities.gateways.AthanorGateway",
    "rooms": "athanor.entities.rooms.AthanorRoom",
    "mobiles": "athanor.entities.mobiles.AthanorMobile",
    "items": "athanor.entities.items.AthanorItem",
    "structures": "athanor.gamedb.structures.AthanorStructure",
    "alliances": "athanor.gamedb.factions.AthanorAlliance",
    "factions": "athanor.gamedb.factions.AthanorFaction",
    "regions": "athanor.gamedb.regions.AthanorRegion",
}


######################################################################
# Account Options
######################################################################
CONTROLLERS['account'] = {
    'class': 'athanor.controllers.account.AthanorAccountController',
}

BASE_ACCOUNT_TYPECLASS = "athanor.gamedb.accounts.AthanorAccount"

# Command set for accounts without a character (ooc)
CMDSET_ACCOUNT = "athanor.cmdsets.account.AthanorAccountCmdSet"


OPTIONS_ACCOUNT_DEFAULT['sys_msg_border'] = ('For -=<>=-', 'Color', 'm')
OPTIONS_ACCOUNT_DEFAULT['sys_msg_text'] = ('For text in sys_msg', 'Color', 'w')
OPTIONS_ACCOUNT_DEFAULT['border_color'] = ("Headers, footers, table borders, etc.", "Color", "M")
OPTIONS_ACCOUNT_DEFAULT['header_star_color'] = ("* inside Header lines.", "Color", "m")
OPTIONS_ACCOUNT_DEFAULT['header_text_color'] = ("Text inside Headers.", "Color", "w")
OPTIONS_ACCOUNT_DEFAULT['column_names_color'] = ("Table column header text.", "Color", "G")


RESTRICTED_ACCOUNT_RENAME = False
RESTRICTED_ACCOUNT_EMAIL = False
RESTRICTED_ACCOUNT_PASSWORD = False

EXAMINE_HOOKS['account'] = ['account', 'access',  'commands', 'tags', 'attributes', 'puppets']

######################################################################
# Character Settings
######################################################################
CONTROLLERS['character'] = {
    'class': 'athanor.controllers.character.AthanorCharacterController',
}

# These restrict a player's ability to create/modify their own characters.
# If True, only staff can perform these operations (if allowed by the privileges system)
RESTRICTED_CHARACTER_CREATION = False
RESTRICTED_CHARACTER_DELETION = False
RESTRICTED_CHARACTER_RENAME = False

# Default set for logged in account with characters (fallback)
CMDSET_CHARACTER = "athanor.cmdsets.character.AthanorCharacterCmdSet"

BASE_CHARACTER_TYPECLASS = "athanor.gamedb.characters.AthanorPlayerCharacter"

# If this is enabled, characters will not see each other's true names.
# Instead, they'll see something generic.
NAME_DUB_SYSTEM = False


EXAMINE_HOOKS['character'] = ['character', 'puppeteer', 'access', 'commands', 'scripts', 'tags', 'attributes', 'contents']



######################################################################
# GameDB Settings
######################################################################
BASE_ROOM_TYPECLASS = "athanor.gamedb.objects.AthanorRoom"

BASE_EXIT_TYPECLASS = "athanor.gamedb.objects.AthanorExit"

BASE_OBJECT_TYPECLASS = "athanor.gamedb.objects.AthanorObject"

######################################################################
# Plugins
######################################################################
GAMEDATA_MODULE_CLASS = "athanor.datamodule.AthanorDataModule"

ATHANOR_PLUGINS = []

# This file needs to be created if it doesn't exist. ATHANOR_PLUGINS should be imported from it, containing a list of
# python paths to desired plugins.
try:
    from server.conf.plugin_settings import *
except ImportError:
    pass

# This property will be filled in by the load process. Don't alter it directly!
ATHANOR_PLUGINS_LOADED = list()

# The Mixins contains lists of python classes to be Added to the base Athanor ones. This is DANGEROUS TERRITORY
# due to the complexities of Multiple Inheritance. Disclaimer here: do not add properties that conflict with others
# as there is no way to control which plugin's mixins will take priority. Mixins are to be used sparingly and
# only for adding unique standalone properties such as new @lazy_property handlers.

# Keep in mind that BASE refers to AbstractGameEntity, which means anything added to it will ALSO reach
# OBJECT and ENTITY.
# Anything that affects OBJECT will also affect CHARACTER, REGION, and STRUCTURE.

# REMEMBER: Multiple Inheritance == HERE BE DRAGONS
CONTROLLER_MIXINS = defaultdict(list)
GAMEDB_MIXINS = defaultdict(list)
MIXINS = defaultdict(list)

# OPERATIONS are the pieces-of-Permissions that govern access to various parts of the Athanor
# API Operations are auto-granted by the stated Permission. Bereft of an included Permission,
# Developers and Superusers are assumed to have all Operations.
# The permission key dictates at what level of the PERMISSION HIERARCHY one automatically
# can perform this operation. Operations are at the Account level.

# This dictionary describes the Evennia Permissions, including which Permissions
# are able to grant/revoke a Permission. If a Permission is not in this dictionary,
# then it cannot be granted through normal commands.
# If no permission(s) is set, only the Superuser can grant it.

PERMISSION_HIERARCHY = [
    "Guest",  # note-only used if GUEST_ENABLED=True
    "Player",
    "Helper",
    "Builder",
    "Gamemaster",
    "Moderator",
    "Admin",
    "Developer",
]

PERMISSIONS = {
    "Helper": {
        "permission": ("Admin"),
        "description": "Those appointed to help players."
    },
    "Builder": {
        "permission": ("Admin"),
        "description": "Can edit and alter the grid, creating new rooms and areas."
    },
    "Gamemaster": {
        "permission": ("Admin"),
        "description": "Can alter game-related character traits like stats, spawn items, grant rewards, puppet mobiles, etc."
    },
    "Moderator": {
        "permission": ("Admin"),
        "description": "Has access to virtually all communications tools for keeping order and enforcing social rules."
    },
    "Admin": {
        "permission": ("Developer"),
        "description": "Can make wide-spread changes to the game, administrate accounts and characters directly."
    },
    "Developer": {
        "description": "Has virtually unlimited power. Can use very dangerous commands."
    }
}

CMDSETS = defaultdict(list)

INLINEFUNC_ENABLED = True

INSTALLED_APPS = list(INSTALLED_APPS)
INSTALLED_APPS.append('athanor')
LOCK_FUNC_MODULES = list(LOCK_FUNC_MODULES)
LOCK_FUNC_MODULES.append("athanor.lockfuncs")

# Redirect the load process through the plugins, passing this module as settings to be further modified.
# This is where most of the Plugin system's magic happens.
athanor.load(sys.modules[__name__])

INSTALLED_APPS = tuple(INSTALLED_APPS)
LOCK_FUNC_MODULES = tuple(LOCK_FUNC_MODULES)

del athanor
del sys
