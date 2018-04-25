"""
The core module settings for Athanor.

Besides storing core plugin settings this module is meant to be imported for accessing the properties like
HANDLERS.
"""

# Every Athanor Module must have a load order in their __init__.py!
# As this is the core, it must precede ALL other modules. Don't set a load order below -1000!
LOAD_ORDER = -1000

# Athanor Modules may add to these settings.py fields.
INSTALLED_APPS = ('athanor.apps.Core', )
LOCK_FUNC_MODULES = ("athanor.funcs.lock", )
INPUT_FUNC_MODULES = ['athanor.funcs.input', ]
INLINE_FUNC_MODULES = ['athanor.funcs.inline', ]

# This dictionary will contain key->instances of all the loaded Athanor modules once loading is complete.
MODULES = dict()

# This tuple will be set by the setup process to contain all of the modules in the order they are to be loaded.
MODULES_ORDER = tuple()

# Dictionary that contains the Types and Python Paths of the Athanor Managers that are to be used.
# This can be overruled by modules that load later.
# Once it has loaded, this will contain key->class instances.
MANAGERS = {
    'character': 'athanor.managers.characters.CharacterManager',
    'account': 'athanor.managers.accounts.AccountManager',
    'session': 'athanor.managers.sessions.SessionManager',
}

# Dictionary that contains the Keys/Names and Python Paths to the Account Handlers for this module.
# Other modules may also implement this dictionary. After the load process, the 'last remaiing' k/v pairs in the
# dictionary will be converted to key->class format.
# Hence, you can 'import athanor' and then access HANDLERS_ACCOUNT[key] to retrieve a class.

HANDLERS_ACCOUNT = {
    'core': 'athanor.handlers.accounts.AccountCoreHandler',
    'who': 'athanor.handlers.accounts.AccountWhoHandler',
    'character': 'athanor.handlers.accounts.AccountCharacterHandler',
}

# Just  like Account but for characters.
HANDLERS_CHARACTER = {
    'core': 'athanor.handlers.characters.CharacterCoreHandler',
    'who': 'athanor.handlers.characters.CharacterWhoHandler',
    'character': 'athanor.handlers.characters.CharacterCharacterHandler'
}

# Same but for sessions.
HANDLERS_SESSION = {
    'core': 'athanor.handlers.sessions.SessionCoreHandler',
}

# Just as with MANAGERS, above. The difference is these are for rendering text output to the given Account/Character.
RENDERERS = {
    'sessions': 'athanor.renderers.sessions.SessionRenderer',
    'character': 'athanor.renderers.characters.CharacterRenderer',
    'account': 'athanor.renderers.accounts.AccountRenderer'
}

# Styles are as to Renderers what Handlers are to the Manager. They are setting collections for handling appearances.
# scripts do not have styles.
STYLES_ACCOUNT = {
    'login': 'athanor.styles.accounts.AccountLoginStyle',
}

STYLES_CHARACTER = {

}

STYLES_SESSION = {

}

# If a color or appearance query is not found in a Style, it will fallback/default to these values.
# Update this dictionary in a further module to change them.
STYLES_FALLBACK = {
    'header_fill_color': 'M',
    'header_star_color': 'w',
    'subheader_fill_color': 'M',
    'subheader_star_color': 'w',
    'separator_fill_color': 'M',
    'separator_star_color': 'w',
    'footer_fill_color': 'M',
    'footer_star_color': 'w',
    'header_text_color': 'w',
    'subheader_text_color': 'w',
    'separator_text_color': 'w',
    'footer_text_color': 'w',
    'border_color': 'M',
    'msg_edge_color': 'M',
    'msg_name_color': 'w',
    'ooc_edge_color': 'R',
    'ooc_prefix_color': 'w',
    'exit_name_color': 'n',
    'exit_alias_color': 'n',
    'table_column_header_text_color': 'G',
    'dialogue_text_color': '',
    'dialogue_quotes_color': '',
    'my_name_color': '',
    'speaker_name_color': '',
    'other_name_color': '',
    'header_fill': '=',
    'subheader_fill': '=',
    'separator_fill': '-',
    'footer_fill': '='
}

# Validators are used for checking user input and returning something the system use, or raising an error if it can't.
# Like everything else in athanor, these can be replaced/overloaded by later modules.
# After load, this will contain the keys pointing to the callable function objects.
VALIDATORS = {
    'color': 'athanor.validators.funcs.valid_color',
    'duration': 'athanor.validators.funcs.valid_duration',
    'datetime': 'athanor.validators.funcs.valid_datetime',
    'signed_integer': 'athanor.validators.funcs.valid_signed_integer',
    'positive_integer': 'athanor.validators.funcs.valid_positive_integer',
    'unsigned_integer': 'athanor.validators.funcs.valid_unsigned_integer',
    'boolean': 'athanor.validators.funcs.valid_boolean',
    'timezone': 'athanor.validators.funcs.valid_timezone',
    'account_email': 'athanor.validators.funcs.valid_account_email',
    'account_name': 'athanor.validators.funcs.valid_account_name',
    'account_password': 'athanor.validators.funcs.valid_account_password',
    'character_name': 'athanor.validators.funcs.valid_character_name',
    'character_id': 'athanor.validators.funcs.valid_character_id',
    'account_id': 'athanor.validators.funcs.valid_account_id',
}

SYSTEMS = {
    'core': 'athanor.systems.scripts.CoreSystem',
    'who': 'athanor.systems.scripts.WhoSystem',
}

# Athanor allows for multiple at_server_start, at_server_stop, etc, hooks to be fired off in sequence.
# Simply add more modules to another module to add to the load process. The default load_athanor is mandatory.
START_STOP = ['athanor.conf.load_athanor',]

INITIAL_SETUP = ['athanor.conf.install_athanor',]

# Core setup stuff below. Don't touch this.

def setup(module_list):
    import importlib
    global plugins, load_order, initial_setup, start_stop
    for plugin in module_list:
        load_plugin = importlib.import_module(plugin)
        plugins[plugin] = load_plugin

    load_order = sorted(plugins.values(), key=lambda m: m.LOAD_ORDER)

    for plugin in load_order:
        if hasattr(plugin, 'INITIAL_SETUP'):
            initial_setup += plugin.INITIAL_SETUP
        if hasattr(plugin, 'START_STOP'):
            start_stop += plugin.START_STOP