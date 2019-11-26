import re
from django.conf import settings
from evennia.typeclasses.models import TypeclassBase
from features.factions.models import FactionDB, FactionLinkDB, FactionRoleDB, FactionPrivilegeDB, FactionRoleLinkDB
from features.core.base import AthanorTypeEntity
from evennia.typeclasses.managers import TypeclassManager
from typeclasses.scripts import GlobalScript
from evennia.utils.validatorfuncs import positive_integer
from utils.valid import simple_name
from evennia.utils.utils import class_from_module
from evennia.utils.logger import log_trace
from utils.text import partial_match

_PERM_RE = re.compile(r"^[a-zA-Z_0-9]+$")


class DefaultFaction(FactionDB, AthanorTypeEntity, metaclass=TypeclassBase):
    objects = TypeclassManager()

    def __init__(self, *args, **kwargs):
        FactionDB.__init__(self, *args, **kwargs)
        AthanorTypeEntity.__init__(self, *args, **kwargs)

    def at_first_save(self, *args, **kwargs):
        pass

    @property
    def ancestors(self):
        full_list = list()
        p = self.parent
        while p is not None:
            full_list.append(p)
            p = p.parent
        full_list.reverse()
        return full_list

    @classmethod
    def validate_key(cls, key_text, rename_from=None, parent=None):
        if not key_text:
            raise ValueError("Factions must have a name!")
        key_text = simple_name(key_text, option_key='Faction Name')
        query = FactionDB.objects.filter_family(db_key__ixact=key_text, db_parent=parent)
        if rename_from:
            query = query.exclude(id=rename_from)
        if query.count():
            raise ValueError("Another Faction already uses that name!")
        return key_text

    @classmethod
    def create(cls, *args, **kwargs):
        parent = kwargs.get('parent', None)
        if parent and not isinstance(parent, FactionDB):
            raise ValueError("Parent must be an instance of a Faction!")

        key = kwargs.get('key', None)
        key = cls.validate_key(key, parent=parent)
        tier = kwargs.get('tier', 0)

        new_faction = cls(db_key=key, db_tier=tier, db_parent=parent)
        new_faction.save()
        return new_faction

    def entity_has_privilege(self, entity, privilege_name, admin_bypass=True):
        if admin_bypass and entity.is_admin:
            return True
        found_privilege = self.privileges.filter(key__iexact=privilege_name).first()
        if not found_privilege:
            return False
        if found_privilege.non_members:
            return True
        membership = self.memberships.filter(db_entity=entity).first()
        if not membership:
            return False
        if found_privilege.all_members:
            return True
        return found_privilege in membership.privileges

    def create_new_membership(self, entity):
        pass

    def delete_membership(self, entity):
        pass

    def create_privilege(self, privilege_name):
        if self.privileges.filter(key__iexact=privilege_name).count():
            pass
        new_privilege, created = self.privileges.get_or_create(key=privilege_name)
        if created:
            new_privilege.save()
        return new_privilege

    def delete_privilege(self, privilege_name):
        found_privilege = self.privileges.filter(key__iexact=privilege_name).first()
        if not found_privilege:
            pass
        found_privilege.delete()

    def create_role(self, role_name):
        if self.roles.filter(key__iexact=role_name).count():
            pass
        new_role, created = self.roles.get_or_create(key=role_name)
        if created:
            new_role.save()
        return new_role

    def delete_role(self, role_name):
        found_role = self.roles.filter(key__iexact=role_name).first()
        if not found_role:
            pass
        found_role.delete()

    def get_child_typeclass(self):
        return self.get_typeclass_field('child_typeclass', settings.BASE_FACTION_TYPECLASS)

    def get_link_typeclass(self):
        return self.get_typeclass_field('link_typeclass', settings.BASE_FACTION_LINK_TYPECLASS)

    def get_privilege_typeclass(self):
        return self.get_typeclass_field('privilege_typeclass', settings.BASE_FACTION_PRIVILEGE_TYPECLASS)

    def get_role_typeclass(self):
        return self.get_typeclass_field('role_typeclass', settings.BASE_FACTION_ROLE_TYPECLASS)

    def get_role_link_typeclass(self):
        return self.get_typeclass_field('role_link_typeclass', settings.BASE_FACTION_ROLE_LINK_TYPECLASS)

    def members(self):
        return self.memberships.filter(db_member=True)


class DefaultFactionLink(FactionLinkDB, AthanorTypeEntity, metaclass=TypeclassBase):
    objects = TypeclassManager()

    def __init__(self, *args, **kwargs):
        FactionLinkDB.__init__(self, *args, **kwargs)
        AthanorTypeEntity.__init__(self, *args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        pass

    def add_role(self, role):
        pass

    def remove_role(self, role):
        pass

    def add_privilege(self, privilege):
        pass

    def remove_privilege(self, privilege):
        pass


class DefaultFactionRole(FactionRoleDB, AthanorTypeEntity, metaclass=TypeclassBase):
    objects = TypeclassManager()

    def __init__(self, *args, **kwargs):
        FactionRoleDB.__init__(self, *args, **kwargs)
        AthanorTypeEntity.__init__(self, *args, **kwargs)


class DefaultFactionPrivilege(FactionPrivilegeDB, AthanorTypeEntity, metaclass=TypeclassBase):
    objects = TypeclassManager()

    def __init__(self, *args, **kwargs):
        FactionPrivilegeDB.__init__(self, *args, **kwargs)
        AthanorTypeEntity.__init__(self, *args, **kwargs)


class DefaultFactionRoleLink(FactionRoleLinkDB, AthanorTypeEntity, metaclass=TypeclassBase):
    objects = TypeclassManager()

    def __init__(self, *args, **kwargs):
        FactionRoleLinkDB.__init__(self, *args, **kwargs)
        AthanorTypeEntity.__init__(self, *args, **kwargs)


class DefaultFactionController(GlobalScript):
    system_name = 'FACTION'
    option_dict = {
    }

    def at_start(self):
        from django.conf import settings
        try:
            self.ndb.faction_typeclass = class_from_module(settings.BASE_FACTION_TYPECLASS,
                                                         defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.ndb.theme_typeclass = DefaultFaction



    def factions(self, parent=None):
        return DefaultFaction.objects.filter_family(db_parent=parent).order_by('-db_tier', 'db_key')

    def find_faction(self, enactor, search_text):
        search_tree = [text.strip() for text in search_text.split('/')] if '/' in search_text else [search_text]
        found = None
        for srch in search_tree:
            found = partial_match(srch, self.factions(found))
            if not found:
                raise ValueError(f"Faction {srch} not found!")
        return found



    def add_main_member(self, enactor, character, rank_int):
        """
        Add a character to the Faction as a main member.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            character (ObjectDB): The character to be added to the Faction.
            rank_int (int): The rank the new member will start at.

        Returns:
            None
        """
        if not self.permission_check(enactor, 'manage'):
            raise ValueError("Permission denied. You lack the 'manage' Permission.")
        if character in self.db.main_members:
            raise ValueError(f"{character} is already a main member of {self}!")
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        if rank_int not in self.db.ranks:
            raise ValueError(f"{rank_int} is not an available Rank.")
        self.db.ranks[rank_int]['members'].add(character)
        self.db.main_members[character] = {
            'rank': rank_int,
            'permissions': (),
            'title': '',
        }
        self.msg_target(enactor, f"You added {character} to the {self}!")
        self.msg_target(character, f"{enactor} added you to the {self}!")
        self.recalculate_basic_membership()

    def remove_main_member(self, enactor, character):
        """
        Remove a main member from the Faction.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            character (ObjectDB): The character to be removed from the Faction.

        Returns:
            None
        """
        if not self.permission_check(enactor, 'manage'):
            raise ValueError("Permission denied. You lack the 'manage' Permission.")
        if character not in self.db.main_members:
            raise ValueError(f"{character} is not a main member of {self}!")
        old_rank = self.db.main_members[character]['rank']
        enactor_rank = self.effective_main_rank(enactor)
        if not (enactor_rank == 0 or enactor_rank < old_rank):
            raise ValueError("Permission denied. You lack sufficient rank.")
        self.db.ranks[old_rank]['members'].remove(character)
        del self.db.main_members[character]
        self.msg_target(enactor, f"You removed {character} from the {self}!")
        self.msg_target(character, f"{enactor} removed you from the {self}!")
        self.recalculate_basic_membership()

    def change_main_member_rank(self, enactor, character, rank_int):
        """
        Promote/demote a Main Member to a different rank.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            character (ObjectDB): The character whose rank is being altered.
            rank_int (int): The new rank for the character.

        Returns:
            None
        """
        if not self.permission_check(enactor, 'manage'):
            raise ValueError("Permission denied. You lack the 'manage' Permission.")
        if character not in self.db.main_members:
            raise ValueError(f"{character} is not a main member of {self}!")
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        if rank_int not in self.db.ranks:
            raise ValueError(f"{rank_int} is not an available Rank.")
        enactor_rank = self.effective_main_rank(enactor)
        old_rank = self.db.main_members[character]['rank']
        if rank_int <= enactor_rank:
            raise ValueError("Cannot grant rank equal to or beyond your own!")
        if not (enactor_rank == 0 or enactor_rank < old_rank):
            raise ValueError("Cannot modify the rank of a superior!")
        self.db.ranks[old_rank]['members'].remove(character)
        self.db.ranks[rank_int]['members'].add(character)
        self.db.main_members[character]['rank'] = rank_int
        self.msg_target(enactor, f"You changed {character}'s rank in {self} to: {rank_int}")
        self.msg_target(character, f"{enactor} changed your rank in {self} to: {rank_int}")

    def create_rank(self, enactor, rank_int, rank_name):
        """
        Create a new rank. Ranks must have unique names and numbers inside a Faction.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            rank_int (int): The number for the new rank.
            rank_name (str): The (unique) name of the new rank.

        Returns:
            None
        """
        enactor_rank = self.effective_main_rank(enactor)
        if not enactor_rank < 2:
            raise ValueError("Permission denied. Only Faction leaders can alter rank structure.")
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        rank_name = simple_name(rank_name, option_key=f"{self.type_name} Rank Names")
        if rank_int in self.db.ranks:
            raise ValueError("Rank Number in use!")
        lower_names = [rank['name'].lower() for rank in self.db.ranks.values()]
        if rank_name.lower() in lower_names:
            raise ValueError("That Rank Name is already in use!")
        self.db.ranks[rank_int] = {
            'name': rank_name,
            'permissions': set(),
            'members': set()
        }
        self.msg_target(enactor, f"You created rank '{rank_int}: {rank_name}' for the {self}")

    def main_members_rank(self, rank_int):
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        return sorted([char for char in self.db.ranks[rank_int]['members'] if char], key=lambda c: str(c))

    def delete_rank(self, enactor, rank_int, rank_name):
        """
        Delete a rank. It must be unused.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            rank_int (int): The number for the rank to be deleted.
            rank_name (str): The (unique) name of the rank. Must be provided for verification.

        Returns:
            None
        """
        enactor_rank = self.effective_main_rank(enactor)
        if not enactor_rank < 2:
            raise ValueError("Permission denied. Only Faction leaders can alter rank structure.")
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        if rank_int < 5:
            raise ValueError("Ranks 1-4 cannot be deleted.")
        rank_name = simple_name(rank_name, option_key=f"{self.type_name} Rank Names")
        if rank_int not in self.db.ranks:
            raise ValueError("Rank not found!")
        exist_name = self.db.ranks[rank_int]['name']
        if rank_name.lower() != exist_name.lower():
            raise ValueError(f"Verification failed! Entered rank name does not match: {exist_name}")
        members = self.main_members_rank(rank_int)
        if members:
            raise ValueError(f"Cannot delete rank. In use by: {', '.join(str(c) for c in members)}")
        del self.db.ranks[rank_int]
        self.msg_target(enactor, f"You deleted {self}'s rank '{rank_int}: {exist_name}")

    def change_rank_permissions(self, enactor, rank_int, change_string):
        """
        Alter what permissions a rank has.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            rank_int (int): The number for the rank to be altered.
            change_string (str): a string of space-separated permission-words to be added.
                Preface a word with a ! to remove it. Example: "manage !moderate" to add
                manage and remove moderate.

        Returns:
            None
        """
        enactor_rank = self.effective_main_rank(enactor)
        if not enactor_rank < 3:
            raise ValueError("Permission denied. Only Faction leader or second in command can alter rank permissions.")
        rank_int = positive_integer(rank_int, option_key=f"{self.type_name} Rank Numbers")
        if not change_string:
            raise ValueError("Nothing entered to change!")
        if rank_int not in self.db.ranks:
            raise ValueError("Rank not found!")
        if rank_int < 3 and '!' in change_string:
            raise ValueError("Cannot remove permissions from Ranks 1-2")
        start_permissions = self.db.ranks[rank_int]['permissions']
        new_permissions = modify_string_set(self.db.permissions, start_permissions, change_string)
        self.db.ranks[rank_int]['permissions'] = new_permissions
        self.msg_target(enactor, f"The {self} rank {rank_int} now has permissions: {', '.join(new_permissions)}")

    def change_main_member_permissions(self, enactor, character, change_string):
        """
        Grant or revoke permissions to a specific member. You can only grant permissions
        that you actually have. Same goes for revoking.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            character (ObjectDB): The character being modified.
            change_string (str): a string of space-separated permission-words to be added.
                Preface a word with a ! to remove it. Example: "manage !moderate" to add
                manage and remove moderate.

        Returns:
            None
        """
        if not self.permission_check(enactor, 'manage'):
            raise ValueError("Permission denied. You lack the 'manage' Permission.")
        if character not in self.db.main_members:
            raise ValueError(f"{character} is not a main member of {self}!")
        enactor_rank = self.effective_main_rank(enactor)
        if enactor_rank < 3:
            available_permissions = self.db.permissions
        else:
            available_permissions = self.get_effective_permissions(enactor)
        start_permissions = self.db.main_members[character]['permissions']
        new_permissions = modify_string_set(available_permissions, start_permissions, change_string)
        self.db.main_members[character]['permissions'] = new_permissions
        perm_string = ', '.join(new_permissions)
        self.msg_target(enactor, f"{character}'s new {self} Permissions are: {perm_string}")
        self.msg_target(character, f"{character} changed your {self} permission set to: {perm_string}")

    def create_permission(self, enactor, perm_name):
        """
        Create a whole new permission. Custom permissions are only useful for locks.
        Permissions must be simple lower-case whole words like 'booya'

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            perm_name (str): The name of the new permission.

        Returns:
            None
        """
        enactor_rank = self.effective_main_rank(enactor)
        if not enactor_rank < 3:
            raise ValueError("Permission denied. Only Faction leader or second in command can alter permissions.")
        if not _PERM_RE.match(perm_name):
            raise ValueError("Permission names must be short alphanumeric strings!")
        perm_name = perm_name.lower()
        perms_lower = [perm.lower() for perm in self.db.permissions]
        if perm_name in perms_lower:
            raise ValueError("Permission of that name already exists!")
        self.db.permissions.add(perm_name)

    def delete_permission(self, enactor, perm_name):
        """
        Delete a custom permission. THe permission must be completely unused within the Faction.
        This can't check for if anything's locks are using this permission though so... be
        careful.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            perm_name (str): The name of the permission being deleted.

        Returns:
            None
        """
        enactor_rank = self.effective_main_rank(enactor)
        if not enactor_rank < 3:
            raise ValueError("Permission denied. Only Faction leader or second in command can alter permissions.")
        if not perm_name:
            raise ValueError("No permission entered to remove!")
        perm_name = perm_name.lower()
        perms_lower = [perm.lower() for perm in settings.FACTION_DEFAULT_BASIC_PERMISSIONS]
        if perm_name in perms_lower:
            raise ValueError("Cannot delete basic permissions!")
        perms_lower = [perm.lower() for perm in self.db.permissions]
        if perm_name not in perms_lower:
            raise ValueError("Permission not found! must use exact name!")
        perms_lower = [perm.lower() for perm in self.db.member_permissions]
        if perm_name in perms_lower:
            raise ValueError("Permission used by Main Member Permissions. Cannot delete!")
        perms_lower = [perm.lower() for perm in self.db.basic_permissions]
        if perm_name in perms_lower:
            raise ValueError("Permission used by Basic Member Permissions. Cannot delete!")
        for rank_int, rank_dict in self.db.ranks.items():
            perms_lower = [perm.lower() for perm in rank_dict['permissions']]
            if perm_name in perms_lower:
                raise ValueError(f"Permission used by Rank {rank_int}. Cannot delete!")
        for char, char_dict in self.db.main_members.items():
            perms_lower = [perm.lower() for perm in char_dict['permissions']]
            if perm_name in perms_lower:
                raise ValueError(f"Permission used by Main Member {char}. Cannot delete!")
        self.db.permissions.remove(perm_name)

    def change_title(self, enactor, character, new_title):
        """
        Change a main member's title.

        Args:
            enactor (ObjectDB): The character whose permissions are to be checked
                for this operation.
            character (ObjectDB): The character whose title is being changed.
            new_title (str): The new title to display.

        Returns:
            None
        """
        if character not in self.db.main_members:
            raise ValueError(f"{character} is not a main member of {self}!")
        if character == enactor:
            if not self.permission_check(enactor, 'manage') or self.permission_check(enactor, 'titleself'):
                raise ValueError("Permission denied. You lack both 'manage' and 'titleself' permissions.")
        else:
            if not self.permission_check(enactor, 'manage'):
                raise ValueError("Permission denied. You lack the 'manage' Permission.")
            enactor_rank = self.effective_main_rank(enactor)
            old_rank = self.db.main_members[character]['rank']
            if not (enactor_rank == 0 or enactor_rank < old_rank):
                raise ValueError("Permission denied. Cannot change the rank of a superior!")
        if not new_title:
            raise ValueError("No title entered to set!")
        self.db.main_members[character]['title'] = new_title
        self.msg_target(enactor, f"You changed {character}'s {self} title to: {new_title}")
        self.msg_target(character, f"{enactor} changed your {self} title to: {new_title}")


    def effective_main_rank(self, character, check_admin=True, check_parent=True):
        """
        Calculates the effective rank of a character. The lower in value, the more powerful
        the rank. Rank 0 is admin/superuser with full control of the Faction.
        Rank 0 can only be obtained by players if they are rank 1-2 of a parent faction.

        Args:
            character (ObjectDB): The character to check.
            check_admin (bool): Whether to check for admin ranks.
            check_parent (bool): Whether to check up the parent chain.

        Returns:
            rank_int (int): The effective rank. None if there is nothing to work with.
        """
        if check_admin:
            if character.locks.check_lockstring(character, "dummy:perm(Admin)"):
                return 0
        if check_parent and self.db.parent:
            parent_rank = self.db.parent.effective_main_rank(character, check_admin=False, check_parent=True)
            if parent_rank < 3:
                return 0
        if character not in self.db.main_members:
            return None
        return self.db.main_members[character]['rank']


    def at_server_reload(self):
        pass
        #self.recalculate_basic_membership()

    def get_basic_members(self):
        """
        Calculates all basic members of this group, including all children
        and their children and etc.

        Returns:
            basic_members (set): of ObjectDBs.
        """
        basic_members = set()
        basic_members.update(self.db.basic_members)
        basic_members.update(set(self.db.main_members.keys()))
        for child in self.all():
            basic_members.update(child.get_basic_members())
        return basic_members

    def recalculate_basic_membership(self):
        """
        Retrieves and caches the basic member list. Used for locks.

        Returns:
            None
        """
        self.ndb.basic_members = self.get_basic_members()

    def get_effective_permissions(self, character):
        """
        Given a character, calculates that character's total permissions.

        Args:
            character (ObjectDB): The character being checked.

        Returns:
            permission_set (set)
        """
        permission_set = set()
        if character not in self.ndb.basic_members:
            return permission_set
        permission_set.update(self.db.basic_permissions)
        if character in self.db.main_members:
            permission_set.update(self.db.member_permissions)
            permission_set.update(self.db.main_members[character]['permissions'])
        return permission_set

    def permission_check(self, character, permission):
        """
        Check whether a given character has a permission or not.
        Characters over a certain rank/admin have all permissions.

        Args:
            character (ObjectDB): The character being checked.
            permission (str): The permission being checked.

        Returns:
            Answer (bool)
        """
        rank = self.effective_main_rank(character)
        if rank < 2:
            return True
        permission_set = self.get_effective_permissions(character)
        return permission in permission_set

    def at_post_move(self):
        self.recalculate_basic_membership()

    def get_display_name(self, viewer=None):
        return f"|{self.options.color}{self.key}|n"

    def get_members_rank(self, rank_int):
        return sorted([member for member in self.db.ranks[rank_int]['members'] if member], key=lambda c: str(c))

    def is_member(self, character):
        if character.locks.check_lockstring(character, "dummy:perm(Admin)"):
            return True
        if character in self.ndb.basic_members:
            return True


