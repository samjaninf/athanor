import athanor
from athanor.base.commands import AthCommand
from athanor.base.handlers import AthanorRequest

# Admin and building commands go here.
class CmdDark(AthCommand):
    """
    When you are Dark, other characters won't be able to see you in the room unless you speak up.

    Usage:
        [PREFIX]dark
        reports your current status. To change...

        [PREFIX]dark/on
        [PREFIX]dark/off
    """

    key = 'dark'
    locks = 'cmd:perm(Admin)'
    help_category = 'Admin'
    admin_switches = ['on', 'off']

    def _main(self):
        self.character.ath['core'].console_msg("Current Dark Status: " % self.character.ath['core'].dark)

    def switch_on(self):
        self.character.ath['core'].dark = True

    def switch_off(self):
        self.character.ath['core'].dark = False





class CharacterCmdOOC(AthCommand):
    """
    stop puppeting and go ooc

    Usage:
        @ooc

    Go out-of-character (OOC).

    This will leave your current character and put you in a incorporeal OOC state.
    """

    key = "@ooc"
    locks = "cmd:pperm(Player)"
    aliases = "@unpuppet"
    help_category = "General"


    def _main(self):

        request = AthanorRequest(session=self.session, handler='core',
                                 operation='puppet_character', parameters={'character_id': 0})
        self.session.ath['core'].accept_request(request)


class CmdLook(AthCommand):
    """
    look at location or object

    Usage:
      look
      look <obj>
      look *<account>

    Observes your location or objects in your vicinity.
    """
    key = "look"
    aliases = ["l", "ls", 'dir']
    locks = "cmd:all()"
    arg_regex = r"\s|$"

    def func(self):
        """
        Handle the looking.
        """
        caller = self.caller
        if not self.args:
            target = caller.location
            if not target:
                caller.msg("You have no location to look at!")
                return
        else:
            target = caller.search(self.args)
            if not target:
                return
        self.msg(caller.at_look(self.session, target))


class CmdHelp(AthCommand):
    """
    Display the Athanor +help menu tree.

    Usage:
       +help
       +help <filename>
       +help <filename>/<subfile>...
    """
    key = '+help'
    locks = "cmd:all()"
    tree = athanor.HELP_TREES['+help']

    def _main(self):
        if not self.lhs:
            self.msg(text=self.tree.display(self.session))
            return
        self.msg(text=self.tree.traverse_tree(self.session, self.lhs_san))


class CmdShelp(CmdHelp):
    key = '+shelp'
    locks = 'cmd:perm(Admin)'
    tree = athanor.HELP_TREES['+shelp']