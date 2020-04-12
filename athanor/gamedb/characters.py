from athanor.gamedb.scripts import AthanorIdentityScript
from athanor.utils.mixins import HasCommands, HasSessions


class AthanorPlayerCharacter(AthanorIdentityScript, HasCommands, HasSessions):
    _namespace = "player_character"
    _verbose_name = 'Player Character'
    _verbose_name_plural = "Player Characters"

    def at_identity_creation(self, validated, kwargs):
        # Should probably do something here about creating ObjectDB's... player avatars. By default.
        pass
