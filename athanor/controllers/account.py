import re
from django.conf import settings

from evennia.utils.utils import class_from_module
from evennia.utils.logger import log_trace
from evennia.utils.search import search_account

import athanor
from athanor.controllers.base import AthanorController
from athanor.gamedb.accounts import AthanorAccount
from athanor.messages import account as amsg

MIXINS = [class_from_module(mixin) for mixin in settings.CONTROLLER_MIXINS["ACCOUNT"]]
MIXINS.sort(key=lambda x: getattr(x, "mixin_priority", 0))


class AthanorAccountController(*MIXINS, AthanorController):
    system_name = 'ACCOUNTS'

    def __init__(self, key, manager):
        AthanorController.__init__(self, key, manager)
        self.account_typeclass = None
        self.id_map = dict()
        self.name_map = dict()
        self.roles = dict()
        self.reg_names = None
    
    def do_load(self):
        try:
            self.account_typeclass = class_from_module(settings.BASE_ACCOUNT_TYPECLASS,
                                                         defaultpaths=settings.TYPECLASS_PATHS)
        except Exception:
            log_trace()
            self.account_typeclass = AthanorAccount

        self.update_cache()
        self.update_roles()

    def update_regex(self):
        escape_names = [re.escape(name) for name in self.name_map.keys()]
        self.reg_names = re.compile(r"(?i)\b(?P<found>%s)\b" % '|'.join(escape_names))

    def update_cache(self):
        accounts = AthanorAccount.objects.filter_family()
        self.id_map = {acc.id: acc for acc in accounts}
        self.name_map = {acc.username.upper(): acc for acc in accounts}
        self.update_regex()

    def update_roles(self):
        for plugin in athanor.CONTROLLER_MANAGER.get('gamedata').plugins_sorted:
            self.roles.update(plugin.data.get("roles", dict()))

    def create_account(self, session, username, email, password, login_screen=False, **kwargs):
        if not login_screen:
            if not (enactor := session.get_account()) or not enactor.check_lock("apriv(account_create)"):
                raise ValueError("Permission denied.")
        new_account = self.account_typeclass.create_account(username=username, email=email, password=password,
                                                                session=session, ip=session.address)
        self.id_map[new_account.id] = new_account
        self.name_map[new_account.username.upper()] = new_account
        self.update_regex()
        if login_screen:
            amsg.CreateMessage(source=session, target=new_account).send()
        else:
            amsg.CreateMessageAdmin(source=enactor, target=new_account, password=password).send()

        return new_account

    def rename_account(self, session, account, new_name, ignore_priv=False):
        if not (enactor := session.get_account()) or (not ignore_priv and not enactor.check_lock("apriv(account_rename)")):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        old_name = str(account)
        new_name = account.rename(new_name)
        amsg.RenameMessage(source=enactor, target=account, old_name=old_name, account_name=new_name).send()

    def change_email(self, session, account, new_email, ignore_priv=False):
        if not (enactor := session.get_account()) or (not ignore_priv and not enactor.check_lock("apriv(account_email)")):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        old_email = account.email
        new_email = account.set_email(new_email)
        amsg.EmailMessage(source=enactor, target=account, old_email=old_email).send()

    def find_account(self, search_text, exact=False):
        if isinstance(search_text, AthanorAccount):
            return search_text
        if '@' in search_text:
            found = AthanorAccount.objects.get_account_from_email(search_text).first()
            if found:
                return found
            raise ValueError(f"Cannot find a user with email address: {search_text}")
        found = search_account(search_text, exact=exact)
        if len(found) == 1:
            return found[0]
        if not found:
            raise ValueError(f"Cannot find a user named {search_text}!")
        raise ValueError(f"That matched multiple accounts: {found}")

    def disable_account(self, session, account, reason):
        if not (enactor := session.get_account()) or not enactor.check_lock("apriv(account_disable)"):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        account.set_unusable_password()
        amsg.DisableMessage(source=enactor, target=account, reason=reason)

    def enable_account(self, session, account, new_password, reason):
        if not (enactor := session.get_account()) or not enactor.check_lock("apriv(account_disable)"):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        if not new_password:
            raise ValueError("Passwords may not be empty!")
        account.set_password(new_password)
        amsg.EnableMessage(source=enactor, target=account, reason=reason)

    def ban_account(self, session, account, duration, reason):
        if not (enactor := session.get_account()) or not enactor.check_lock("apriv(account_ban)"):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        amsg.BanMessage(source=enactor, target=account, duration=duration, reason=reason)

    def unban_account(self, session, account, reason):
        if not (enactor := session.get_account()) or not enactor.check_lock("apriv(account_ban)"):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        amsg.UnBanMessage(source=enactor, target=account, reason=reason)

    def reset_password(self, session, account, new_password, ignore_priv=False, old_password=None):
        if not (enactor := session.get_account()) or (not ignore_priv and not enactor.check_lock("apriv(account_password)")):
            raise ValueError("Permission denied.")
        if ignore_priv and not account.check_password(old_password):
            raise ValueError("Permission denied. Password was incorrect.")
        account = self.find_account(account)
        if not new_password:
            raise ValueError("Passwords may not be empty!")
        account.set_password(new_password)
        if old_password:
            amsg.PasswordMessagePrivate(source=enactor).send()
        else:
            amsg.PasswordMessageAdmin(source=enactor, target=account, password=new_password).send()

    def grant_role(self, session, account, role_key):
        if not (enactor := session.get_account()):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        role = self.find_role(role_key)
        role_lock = role.get("lock", f"perm({settings.ACCOUNT_ROLE_PERMISSION})")
        if not enactor.check_lock(role_lock):
            raise ValueError("Permission denied.")
        account.roles.add(role_key)
        amsg.GranteMessage(source=enactor, target=account, role=role)

    def revoke_role(self, session, account, role_key):
        if not (enactor := session.get_account()):
            raise ValueError("Permission denied.")
        account = self.find_account(account)
        role = self.find_role(role_key)
        role_lock = role.get("lock", f"perm({settings.ACCOUNT_ROLE_PERMISSION})")
        if not enactor.check_lock(role_lock):
            raise ValueError("Permission denied.")
        account.roles.remove(role_key)
        amsg.RevokeMessage(source=enactor, target=account, role=role)