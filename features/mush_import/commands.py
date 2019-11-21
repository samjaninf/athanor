

import MySQLdb
import MySQLdb.cursors as cursors
import datetime
import pytz
import random

from django.conf import settings
from evennia.utils import create
from evennia import GLOBAL_SCRIPTS
from django.db.models import Q

from features.forum.models import ForumCategoryDB
from . convpenn import PennParser, process_penntext
from . models import MushObject, cobj, pmatch, objmatch, MushAttributeName, MushAttribute
from utils.text import partial_match, dramatic_capitalize, sanitize_string, penn_substitutions
from utils.time import utcnow, duration_from_string
from features.core.command import AthanorCommand


def from_unixtimestring(secs):
    try:
        convert = datetime.datetime.fromtimestamp(int(secs)).replace(tzinfo=pytz.utc)
    except ValueError:
        return None
    return convert


def from_mushtimestring(timestring):
    try:
        convert = datetime.datetime.strptime(timestring, '%c').replace(tzinfo=pytz.utc)
    except ValueError:
        return None
    return convert


class CmdPennImport(AthanorCommand):
    key = '@penn'
    system_name = 'IMPORT'
    locks = 'cmd:perm(Developers)'
    admin_switches = ['initialize', 'areas', 'grid', 'accounts', 'groups', 'bbs', 'ex2', 'ex3', 'experience', 'themes', 'radio',
                      'jobs', 'scenes']
    
    def report_status(self, message):
        print(message)
        self.sys_msg(message)
    
    def sql_cursor(self):
        if hasattr(self, 'cursor'):
            return self.cursor
        sql_dict = settings.PENNMUSH_SQL_DICT
        self.sql = MySQLdb.connect(host=sql_dict['site'], user=sql_dict['username'],
                             passwd=sql_dict['password'], db=sql_dict['database'], cursorclass=cursors.DictCursor)
        self.cursor = self.sql.cursor()
        return self.cursor

    def at_post_cmd(self):
        if hasattr(self, 'sql'):
            self.sql.close()

    def switch_initialize(self):
        try:
            mush_import = PennParser('outdb', self.report_status)
        except IOError as err:
            self.error(str(err))
            self.error("Had an IOError. Did you put the outdb in the game's root directory?")
            return
        except ValueError as err:
            self.error(str(err))
            return

        penn_objects = mush_import.mush_data

        obj_dict = dict()

        dbrefs = sorted(penn_objects.keys(), key=lambda dbr: int(dbr.strip('#')))
        db_count = len(dbrefs)
        for count, entity in enumerate(dbrefs, start=1):
            penn_data = penn_objects[entity]
            self.report_status(f"Processing MushObject {count} of {db_count} - {penn_data['objid']}: {penn_data['name']}")
            entry, created = MushObject.objects.get_or_create(dbref=entity, objid=penn_data['objid'],
                                                              type=penn_data['type'], name=penn_data['name'],
                                                              flags=penn_data['flags'], powers=penn_data['powers'],
                                                              created=from_unixtimestring(penn_data['created']))
            if created:
                entry.save()

            obj_dict[entity] = entry

        def set_attr(penn_data, entry, attr, target):
            try:
                if penn_data[attr] in obj_dict:
                    setattr(entry, target, obj_dict[penn_data[attr]])
            except Exception as e:
                self.report_status(f"ERROR DETECTED ON {penn_data}: {entry}, {attr} -> {target}")
                raise e

        for counter, entity in enumerate(dbrefs, start=1):
            penn_data = penn_objects[entity]
            entry = obj_dict[entity]
            self.report_status(f"Performing Secondary Processing on MushObject {counter} of {db_count} - {entry.objid}: {entry.name}")
            for attr, target in (('parent', 'parent'), ('owner', 'owner')):
                set_attr(penn_data, entry, attr, target)

            if penn_data['type'] == 4:  # For exits!
                for attr, target in (('location', 'destination'), ('exits', 'location')):
                    set_attr(penn_data, entry, attr, target)
            else:
                set_attr(penn_data, entry, 'location', 'location')
            entry.save()

            attr_dict = dict()

            for attr, value in penn_data['attributes'].items():
                attr_upper = attr.upper()
                if attr_upper in attr_dict:
                    attr_name = attr_dict[attr_upper]
                else:
                    attr_name, created = MushAttributeName.objects.get_or_create(key=attr_upper)
                    if created:
                        attr_name.save()
                    attr_dict[attr_upper] = attr_name
                attr_entry, created2 = entry.attrs.get_or_create(attr=attr_name, value=penn_substitutions(value))
                if not created2:
                    attr_entry.save()

        self.report_status(f"Imported {db_count} MushObjects and {MushAttribute.objects.count()} MushAttributes into Django. Ready for additional operations.")

    def switch_area_recursive(self, district, parent=None):
        area = district.area
        if not area:
            area = GLOBAL_SCRIPTS.area.create_area(self.session, district.name, parent=parent)
            district.area = area
            district.save()
            self.report_status(f"Created Area: {area.full_path()}")
            for dist in district.children.filter(type=2).order_by('name'):
                self.switch_area_recursive(dist, area)

    def switch_areas(self):
        district_parent = cobj('district')
        for district in district_parent.children.filter(type=2).order_by('name'):
            self.switch_area_recursive(district, parent=None)
        self.report_status("All done with Areas!")

    def switch_grid(self):
        area_con = GLOBAL_SCRIPTS.area
        mush_rooms = MushObject.objects.filter(type=1, obj=None).exclude(Q(parent=None) | Q(parent__area=None))

        mush_rooms_count = len(mush_rooms)

        for counter, mush_room in enumerate(mush_rooms, start=1):
            self.report_status(f"Processing Room {counter} of {mush_rooms_count} - {mush_room.objid}: {mush_room.name}")
            new_room, errs = area_con.create_room(self.session, mush_room.parent.area, mush_room.name, self.account)
            mush_room.obj = new_room
            mush_room.obj.db.desc = process_penntext(mush_room.mushget('DESCRIBE'))
            mush_room.save()


        mush_exits = MushObject.objects.filter(type=4, obj=None).exclude(Q(location__parent__area=None) | Q(destination__parent__area=None) | Q(location__obj=None) | Q(destination__obj=None))
        mush_exits_count = len(mush_exits)

        for counter, mush_exit in enumerate(mush_exits, start=1):
            self.report_status(f"Processing Exit {counter} of {mush_exits_count} - {mush_exit.objid}: {mush_room.name} FROM {mush_exit.location.name} TO {mush_exit.destination.name}")
            aliases = None
            alias_text = mush_exit.mushget('alias')
            if alias_text:
                aliases = alias_text.split(';')

            new_exit, errs = area_con.create_exit(self.session, mush_exit.location.parent.area, mush_exit.name,
                                                  self.account, mush_exit.location.obj, mush_exit.destination.obj,
                                                  aliases=aliases)
            mush_exit.obj = new_exit
            mush_exit.save()

    def random_password(self):
        password = "ABCDEFGHabcdefgh@+-" + str(random.randrange(5000000, 1000000000))
        password_list = list(password)
        random.shuffle(password_list)
        password = ''.join(password_list)
        return password

    def switch_accounts(self):
        accounts_con = GLOBAL_SCRIPTS.accounts
        mush_accounts = cobj(abbr='accounts').children.filter(account=None)
        mush_accounts_count = len(mush_accounts)
        for counter, mush_acc in enumerate(mush_accounts, start=1):
            password = self.random_password()
            username = f"mush_acc_{mush_acc.dbref.strip('#')}"
            old_email = mush_acc.mushget('email')
            email = f"{username}@ourgame.org"
            self.report_status(f"Processing Account {counter} of {mush_accounts_count} - {mush_acc.objid}: {mush_acc.name} / {old_email}. New username: {username} - Password: {password}")
            new_account, errors = accounts_con.create_account(self.session, username, email, password)
            mush_acc.account = new_account
            mush_acc.save()
            new_account.db._penn_import = True
            new_account.db._penn_name = mush_acc.name
            new_account.db._penn_email = old_email
        self.report_status(f"Imported {mush_accounts_count} PennMUSH Accounts!")

    def get_lost_and_found(self):
        try:
            lost_and_found = GLOBAL_SCRIPTS.accounts.find_account("LostAndFound")
        except:
            lost_and_found, errors = GLOBAL_SCRIPTS.accounts.create_account(self.session, "LostAndFound", 'dummy@dummy.com',
                                                                            self.random_password())
            lost_and_found.db._lost_and_found = True
        return lost_and_found

    def switch_characters(self):
        lost_and_found = self.get_lost_and_found()
        self.report_status(f"Acquired Lost and Found Account: {lost_and_found}")
        chars_con = GLOBAL_SCRIPTS.characters
        mush_characters = MushObject.objects.filter(type=8, obj=None).exclude(powers__icontains='Guest')
        mush_characters_count = len(mush_characters)

        for counter, mush_char in enumerate(mush_characters, start=1):
            self.report_status(f"Processing Character {counter} of {mush_characters_count} - {mush_char.objid}: {mush_char.name}")
            if mush_char.parent and  mush_char.parent.account:
                acc = mush_char.parent.account
                self.report_status(f"Account Found! Will assign to Account: {acc}")
            else:
                acc = lost_and_found
                self.report_status("Character has no Account! Will assign to Lost and Found!")

            new_char, errors = chars_con.create_character(self.session, acc, mush_char.name)
            mush_char.obj = new_char
            mush_char.save()
            new_char.db._penn_import = True

            for alias in mush_char.aliases():
                new_char.aliases.add(alias)
            description = process_penntext(mush_char.mushget('DESCRIBE'))
            if description:
                self.report_status(f"FOUND DESCRIPTION: {description}")
                new_char.db.desc = description

            flags = mush_char.flags.split(' ')

            if acc != lost_and_found:
                set_super = mush_char.dbref == '#1'
                set_developer = 'WIZARD' in flags
                set_admin = 'ROYALTY' in flags or int(mush_char.mushget('V`ADMIN', default='0'))
                if set_super:
                    acc.is_superuser = True
                    acc.save()
                    set_developer = False
                    set_admin = False
                    self.report_status(f"Detected #1 GOD. {acc} and {new_char} has been granted Superuser privileges.")
                if set_developer:
                    acc.permissions.add('Developer')
                    set_admin = False
                    self.report_status(f"Detected WIZARD flag. {acc} and {new_char} has been granted Developer privileges.")
                if set_admin:
                    acc.permissions.add('Admin')
                    self.report_status(f"Detected ROYALTY flag or Admin Group Membership. {acc} and {new_char} has been granted Admin privileges.")

        self.report_status(f"Finished importing {mush_characters_count} characters!")

    def switch_groups(self):
        faction_con = GLOBAL_SCRIPTS.faction
        c = self.sql_cursor()
        c.execute("""SELECT * FROM volv_group """)
        mush_groups = c.fetchall()

        mush_groups_dict = {i['group_id']: i for i in mush_groups}

        faction_map = dict()

        c.execute("""SELECT * FROM volv_group_member""")

        mush_groups_members = c.fetchall()

        c.execute("""SELECT * FROM volv_group_rank""")

        mush_groups_ranks = c.fetchall()



        minor, cr = GroupCategory.objects.get_or_create(key='Minor', description='Minor Groups', order=1)
        major, cr2 = GroupCategory.objects.get_or_create(key='Major', description='Major Groups', order=2)
        penn_groups = cobj('gop').children.all()
        for old_group in penn_groups:
            if not old_group.group:
                cat = old_group.mushget('SET`MAJOR') or '0'
                cat = int(cat)
                if cat:
                    cat = major
                else:
                    cat = minor
                old_group.group, created = Group.objects.get_or_create(key=old_group.name, category=cat)
                old_group.save(update_fields=['group'])
            new_group = old_group.group
            new_group.description = old_group.mushget('DESCRIBE')
            old_ranks = old_group.lattrp('RANK`\d+')
            old_rank_nums = [old_rank.split('`', 1)[1] for old_rank in old_ranks]
            rank_dict = dict()
            for num in old_rank_nums:
                new_rank, created = new_group.ranks.get_or_create(num=int(num))
                rank_name = old_group.mushget('RANK`%s`NAME' % num)
                if rank_name:
                    new_rank.name = sanitize_string(rank_name)
                    new_rank.save(update_fields=['name'])
                rank_dict[int(num)] = new_rank
            old_members = [objmatch(member) for member in old_group.mushget('MEMBERS').split(' ') if objmatch(member)]
            for old_member in old_members:
                if not old_member.obj:
                    continue
                old_num = int(old_member.mushget('D`GROUP`%s`RANK' % old_group.dbref)) or 4
                title = old_member.mushget('D`GROUP`%s`NAME' % old_group.dbref)
                if not title:
                    title = None
                new_member, created = new_group.participants.get_or_create(character=old_member.obj, title=title,
                                                                           rank=rank_dict[old_num])
                for channel in [new_group.ic_channel, new_group.ooc_channel]:
                    if channel:
                        if channel.locks.check(new_member.character, 'listen'):
                            channel.connect(new_member.character)
            new_group.save()
            board_group, created = BoardGroup.objects.get_or_create(main=0, group=new_group)
            for old_board in old_group.contents.all():
                if not old_board.board:
                    old_board.board = board_group.make_board(key=old_board.name)
                    old_board.save(update_fields=['board'])
                new_board = old_board.board
                old_order = int(old_board.mushget('ORDER'))
                new_board.order = old_order
                new_board.save()
                self.convert_board(new_board)

    def switch_bbs(self):
        penn_boards = cobj('bbs').contents.all()
        board_group, created5 = BoardGroup.objects.get_or_create(main=1, group=None)
        for old_board in penn_boards:
            if not old_board.board:
                old_board.board = board_group.make_board(key=old_board.name)
                old_board.save(update_fields=['board'])
            new_board = old_board.board
            old_order = int(old_board.mushget('ORDER'))
            new_board.order = old_order
            new_board.save()
            self.convert_board(new_board)

    def convert_board(self, new_board):
        old_board = new_board.mush
        old_posts = new_board.mush.lattr('~`*')
        old_dict = dict()
        for old_post in old_posts:
            post_details = old_board.mushget(old_post + '`DETAILS').split('|')
            poster_name = post_details[0]
            poster_objid = post_details[1]
            poster_obj = objmatch(poster_objid)
            if poster_obj:
                owner = poster_obj.obj
            else:
                owner = create.create_object(typeclass='classes.characters.BaseCharacter', key=poster_name)
                dbref, csecs = poster_objid.split(':', 1)
                cdate = from_unixtimestring(csecs)
                MushObject.objects.create(objid=poster_objid, dbref=dbref, created=cdate, type=8, recreated=1, obj=owner)
            post_date = from_unixtimestring(post_details[2])
            text = old_board.mushget(old_post)
            timeout_secs = int(old_board.mushget(old_post + '`TIMEOUT'))
            new_timeout = datetime.timedelta(0, timeout_secs, 0, 0, 0, 0, 0)
            subject = old_board.mushget(old_post + '`HDR')
            old_dict[old_post] = {'subject': subject, 'owner': owner, 'timeout': new_timeout,
                                  'creation_date': post_date, 'text': text}
        for num, old_post in enumerate(sorted(old_posts, key=lambda old: old_dict[old]['creation_date'])):
            old_data = old_dict[old_post]
            new_board.posts.create(subject=old_data['subject'], owner=old_data['owner'],
                                   creation_date=old_data['creation_date'], timeout=old_data['timeout'],
                                   text=old_data['text'], order=num+1)

    def switch_themes(self):
        theme_con = GLOBAL_SCRIPTS.theme
        c = self.sql_cursor()
        c.execute("""SELECT * FROM volv_theme """)
        mush_themes = c.fetchall()
        c.execute("""SELECT * FROM volv_theme_member""")
        mush_theme_members = c.fetchall()

        theme_map = dict()

        mush_theme_count = len(mush_themes)

        for counter, mush_theme in enumerate(mush_themes, start=1):
            self.report_status(f"Processing MushTheme {counter} of {mush_theme_count} - {mush_theme['theme_name']}")
            theme = theme_con.create_theme(self.session, mush_theme['theme_name'], process_penntext(mush_theme['theme_description']))
            theme_map[mush_theme['theme_id']] = theme

        mush_theme_members_count = len(mush_theme_members)

        for counter, mush_theme_member in enumerate(mush_theme_members, start=1):
            self.report_status(f"Processing MushThemeMembership {counter} of {mush_theme_members_count} - {mush_theme_member}")
            character = pmatch(mush_theme_member['character_objid'])
            if not character:
                continue
            theme = theme_map[mush_theme_member['theme_id']]
            list_type = mush_theme_member['tmember_type']
            theme.add_character(character, list_type)
            character.db.theme_status = mush_theme_member['character_status']

    def switch_radio(self):
        pass

    def switch_ex2(self):
        characters = [char for char in Ex2Character.objects.filter_family() if hasattr(char, 'mush')]
        for char in characters:
            self.convert_ex2(char)

    def convert_ex2(self, character):
        # First, let's convert templates.
        template = character.mush.getstat('D`INFO', 'Class') or 'Mortal'


        sub_class = character.mush.getstat('D`INFO', 'Caste') or None
        attribute_string = character.mush.mushget('D`ATTRIBUTES') or ''
        skill_string = character.mush.mushget('D`ABILITIES') or ''
        paths_string = character.mush.mushget('D`PATHS') or ''
        colleges_string = character.mush.mushget('D`COLLEGES') or ''
        virtues_string = character.mush.mushget('D`VIRTUES') or ''
        graces_string = character.mush.mushget('D`GRACES') or ''
        slots_string = character.mush.mushget('D`SLOTS') or ''
        specialties_string = character.mush.mushget('D`SPECIALTIES')
        power = character.mush.getstat('D`INFO', 'POWER') or 1
        power_string = 'POWER~%s' % power
        willpower = character.mush.getstat('D`INFO', 'WILLPOWER')
        if willpower:
            willpower_string = 'WILLPOWER~%s' % willpower
        else:
            willpower_string = ''
        stat_string = "|".join([attribute_string, skill_string, paths_string, colleges_string, virtues_string,
                                graces_string, slots_string, willpower_string, power_string])
        stat_list = [element for element in stat_string.split('|') if len(element)]
        stats_dict = dict()
        for stat in stat_list:
            name, value = stat.split('~', 1)
            try:
                int_value = int(value)
            except ValueError:
                int_value = 0
            stats_dict[name] = int(int_value)

        cache_stats = character.stats.cache_stats

        character.template.swap(template)
        character.template.template.sub_class = sub_class
        character.template.save()

        for stat in stats_dict.keys():
            find_stat = partial_match(stat, cache_stats)
            if not find_stat:
                continue
            find_stat.current_value = stats_dict[stat]
        character.stats.save()

        merits_dict = {'D`MERITS`*': character.storyteller.merits, 'D`FLAWS`*': character.storyteller.flaws,
                       'D`POSITIVE_MUTATIONS`*': character.storyteller.positivemutations,
                       'D`NEGATIVE_MUTATIONS`*': character.storyteller.negativemutations,
                       'D`RAGE_MUTATIONS`*': character.storyteller.ragemutations,
                       'D`WARFORM_MUTATIONS`*': character.storyteller.warmutations,
                       'D`BACKGROUNDS`*': character.storyteller.backgrounds}

        for merit_type in merits_dict.keys():
            self.ex2_merits(character, merit_type, merits_dict[merit_type])

        character.merits.save()

        for charm_attr in character.mush.lattr('D`CHARMS`*'):
            root, charm_name, charm_type = charm_attr.split('`')
            if charm_type == 'SOLAR':
                self.ex2_charms(character, charm_attr, character.storyteller.solarcharms)
            if charm_type == 'LUNAR':
                self.ex2_charms(character, charm_attr, character.storyteller.lunarcharms)
            if charm_type == 'ABYSSAL':
                self.ex2_charms(character, charm_attr, character.storyteller.abyssalcharms)
            if charm_type == 'INFERNAL':
                self.ex2_charms(character, charm_attr, character.storyteller.infernalcharms)
            if charm_type == 'SIDEREAL':
                self.ex2_charms(character, charm_attr, character.storyteller.siderealcharms)
            if charm_type == 'TERRESTRIAL':
                self.ex2_charms(character, charm_attr, character.storyteller.terrestrialcharms)
            if charm_type == 'ALCHEMICAL':
                self.ex2_charms(character, charm_attr, character.storyteller.alchemicalcharms)
            if charm_type == 'RAKSHA':
                self.ex2_charms(character, charm_attr, character.storyteller.rakshacharms)
            if charm_type == 'SPIRIT':
                self.ex2_charms(character, charm_attr, character.storyteller.spiritcharms)
            if charm_type == 'GHOST':
                self.ex2_charms(character, charm_attr, character.storyteller.ghostcharms)
            if charm_type == 'JADEBORN':
                self.ex2_charms(character, charm_attr, character.storyteller.jadeborncharms)
            if charm_type == 'TERRESTRIAL_MARTIAL_ARTS':
                self.ex2_martial(character, charm_attr, character.storyteller.terrestrialmartialarts)
            if charm_type == 'CELESTIAL_MARTIAL_ARTS':
                self.ex2_martial(character, charm_attr, character.storyteller.celestialmartialarts)
            if charm_type == 'SIDEREAL_MARTIAL_ARTS':
                self.ex2_martial(character, charm_attr, character.storyteller.siderealmartialarts)


        for spell_attr in character.mush.lattr('D`SPELLS`*'):
            root, charm_name, charm_type = spell_attr.split('`')
            if charm_type in ['TERRESTRIAL', 'CELESTIAL', 'SOLAR']:
                self.ex2_spells(character, spell_attr, character.storyteller.sorcery)
            if charm_type in ['SHADOWLANDS', 'LABYRINTH', 'VOID']:
                self.ex2_spells(character, spell_attr, character.storyteller.necromancy)

        for spell_attr in character.mush.lattr('D`PROTOCOLS`*'):
            root, charm_name, charm_type = spell_attr.split('`')
            self.ex2_spells(character, spell_attr, character.storyteller.protocols)

        languages = character.mush.mushget('D`LANGUAGES')
        if languages:
            Language = character.storyteller.languages.custom_type
            language_list = languages.split('|')
            for language in language_list:
                new_lang = Language(name=language)
                character.advantages.cache_advantages.add(new_lang)

        character.advantages.save()

    def ex2_merits(self, character, merit_type, merit_class):
        for old_attrs in character.mush.lattr(merit_type):
            old_name = character.mush.mushget(old_attrs)
            old_rank = character.mush.mushget(old_attrs + '`RANK')
            old_context = character.mush.mushget(old_attrs + '`CONTEXT')
            make_class = merit_class.custom_type
            new_merit = make_class(name=old_name, context=old_context, value=old_rank)
            character.merits.cache_merits.add(new_merit)


    def ex2_charms(self, character, attribute, charm_class):
        for charm_attr in character.mush.lattr(attribute + '`*'):
            a_root, charm_root, splat_root, charm_type = charm_attr.split('`')
            charm_dict = dict()
            if not character.mush.mushget(charm_attr):
                continue
            for charm in character.mush.mushget(charm_attr).split('|'):
                charm_name, charm_purchases = charm.split('~', 1)
                charm_purchases = int(charm_purchases)
                charm_dict[charm_name] = charm_purchases
                for prep_charm in charm_dict.keys():
                    new_charm = charm_class(name=prep_charm, sub_category=charm_type.replace('_', ' '))
                    new_charm.current_value = charm_dict[prep_charm]
                    character.advantages.cache_advantages.add(new_charm)


    def ex2_martial(self, character, attribute, martial_class):
        martial_class = martial_class.custom_type
        for count, charm_attr in enumerate(character.mush.lattr(attribute + '`*')):
            style_name = character.mush.mushget(charm_attr + '`NAME') or 'Unknown Style %s' % str(count+1)
            charm_dict = dict()
            for charm in character.mush.mushget(charm_attr).split('|'):
                if charm:
                    charm_name, charm_purchases = charm.split('~', 1)
                    charm_purchases = int(charm_purchases)
                    charm_dict[charm_name] = charm_purchases
                    for prep_charm in charm_dict.keys():
                        new_charm = martial_class(name=prep_charm, custom_category=style_name)
                        new_charm.current_value = charm_dict[prep_charm]
                        character.advantages.cache_advantages.add(new_charm)


    def ex2_spells(self, character, attribute, spell_class):
        attr_root, attr_spell, spell_type = attribute.split('`')
        charm_dict = dict()
        spell_class = spell_class.custom_type
        for charm in character.mush.mushget(attribute).split('|'):
            charm_name, charm_purchases = charm.split('~', 1)
            charm_purchases = int(charm_purchases)
            charm_dict[charm_name] = charm_purchases
            for prep_charm in charm_dict.keys():
                new_charm = spell_class(name=prep_charm, sub_category=spell_type)
                new_charm.current_value = charm_dict[prep_charm]
                character.advantages.cache_advantages.add(new_charm)

    def switch_ex3(self):
        characters = [char for char in Ex3Character.objects.filter_family() if hasattr(char, 'mush')]
        for char in characters:
            self.convert_ex3(char)

        self.ex3_experience()

    def convert_ex3(self, character):
        # First, let's convert templates.
        template = character.mush.getstat('D`INFO', 'Class') or 'Mortal'

        sub_class = character.mush.getstat('D`INFO', 'Caste') or None
        attribute_string = character.mush.mushget('D`ATTRIBUTES') or ''
        skill_string = character.mush.mushget('D`ABILITIES') or ''
        special_string = character.mush.mushget('D`SPECIALTIES')
        power = character.mush.getstat('D`INFO', 'POWER') or 1
        power_string = 'POWER~%s' % power
        willpower = character.mush.getstat('D`INFO', 'WILLPOWER')
        if willpower:
            willpower_string = 'WILLPOWER~%s' % willpower
        else:
            willpower_string = ''
        stat_string = "|".join([attribute_string, skill_string, willpower_string, power_string])
        stat_list = [element for element in stat_string.split('|') if len(element)]
        stats_dict = dict()
        for stat in stat_list:
            name, value = stat.split('~', 1)
            try:
                int_value = int(value)
            except ValueError:
                int_value = 0
            stats_dict[name] = int(int_value)

        character.setup_storyteller()
        character.storyteller.swap_template(template)
        try:
            character.storyteller.set('Caste', sub_class)
        except:
            pass

        new_stats = character.storyteller.stats.all()

        custom_dict = {'D`CRAFTS': 'craft', 'D`STYLES': 'style'}
        for k, v in custom_dict.iteritems():
            self.ex3_custom(character, k, v)

        for special in special_string.split('|'):
            if not len(special) > 2:
                continue
            stat_name, spec_name = special.split('/', 1)
            spec_name, value = spec_name.split('~', 1)
            find_stat = partial_match(stat_name, new_stats)
            if find_stat:
                find_stat.specialize(dramatic_capitalize(spec_name), value)

        favored_string = character.mush.mushget('D`FAVORED`ABILITIES') + '|' + character.mush.mushget('D`FAVORED`ATTRIBUTES')
        supernal_string = character.mush.mushget('D`SUPERNAL`ABILITIES')

        for k, v in stats_dict.iteritems():
            find_stat = partial_match(k, new_stats)
            if not find_stat:
                continue
            find_stat.rating = v
            find_stat.save()

        merits_dict = {'D`MERITS`*': 'merit', 'D`FLAWS`*': 'flaw'}
        for k, v in merits_dict.iteritems():
            self.ex3_merits(character, k, v)

        charms_dict = {'D`CHARMS`SOLAR': 'solar_charm', 'D`CHARMS`LUNAR': 'lunar_charm',
                       'D`CHARMS`ABYSSAL': 'abyssal_charm'}
        for k, v in charms_dict.iteritems():
            self.ex3_charms(character, k, v)


        self.ex3_spells(character)

    def ex3_merits(self, character, merit_type, merit_class):
        sheet_section = character.story.sheet_dict[merit_class]
        for old_attrs in character.mush.lattr(merit_type):
            old_name = character.mush.mushget(old_attrs)
            old_context = character.mush.mushget(old_attrs + '`CONTEXT')
            old_rank = int(character.mush.mushget(old_attrs + '`RANK'))
            old_description = character.mush.mushget(old_attrs + '`DESC')
            old_notes = character.mush.mushget(old_attrs + '`NOTES')
            new_merit = sheet_section.add(old_name, old_context, old_rank)
            new_merit.description = old_description
            new_merit.notes = old_notes
            new_merit.save()

    def ex3_custom(self, character, custom_attr, custom_kind):
        sheet_section = character.story.sheet_dict[custom_kind]
        customs = character.mush.mushget(custom_attr)
        if not customs:
            return
        customs_dict = dict()
        customs = customs.split('|')
        for custom in customs:
            cust_name, cust_dots = custom.split('~', 1)
            cust_dots = int(cust_dots)
            customs_dict[cust_name] = cust_dots
        for k, v in customs_dict.iteritems():
            sheet_section.set(k, v)

    def ex3_charms(self, character, attribute, charm_class):
        sheet_section = character.story.sheet_dict[charm_class]
        for charm_attr in character.mush.lattr(attribute + '`*'):
            charm_type = charm_attr.split('`')[-1]
            charm_dict = dict()
            if not character.mush.mushget(charm_attr):
                continue
            for charm in character.mush.mushget(charm_attr).split('|'):
                charm_name, charm_purchases = charm.split('~', 1)
                charm_purchases = int(charm_purchases)
                charm_dict[charm_name] = charm_purchases
            for k, v in charm_dict.iteritems():
                sheet_section.add(charm_type, k, v)

    def ex3_martial(self, character, attribute, martial_class):
        sheet_section = character.story.sheet_dict[martial_class]
        for count, charm_attr in enumerate(character.mush.lattr(attribute + '`*')):
            style_name = character.mush.mushget(charm_attr + '`NAME') or 'Unknown Style %s' % str(count + 1)
            charm_dict = dict()
            for charm in character.mush.mushget(charm_attr).split('|'):
                if charm:
                    charm_name, charm_purchases = charm.split('~', 1)
                    charm_purchases = int(charm_purchases)
                    charm_dict[charm_name] = charm_purchases
            for k, v in charm_dict.iteritems():
                sheet_section.add(style_name, k, v)

    def ex3_spells(self, character):
        attr_list = [attr for attr in character.mush.lattr('D`SPELLS`*')]
        for attr in attr_list:
            category = attr.split('`')[-1]
            if category in ('TERRESTRIAL', 'CELESTIAL', 'SOLAR'):
                kind = 'sorcery_spell'
            else:
                kind = 'necromancy_spell'
            charm_dict = dict()
            sheet_section = character.story.sheet_dict[kind]
            for charm in character.mush.mushget(attr).split('|'):
                charm_name, charm_purchases = charm.split('~', 1)
                charm_purchases = int(charm_purchases)
                charm_dict[charm_name] = charm_purchases
            for k, v in charm_dict.iteritems():
                sheet_section.add(category, k, v)

    def ex3_experience(self):
        from commands.mysql import sql_dict
        from world.database.storyteller.models import Game
        db = MySQLdb.connect(host=sql_dict['site'], user=sql_dict['username'],
                             passwd=sql_dict['password'], db=sql_dict['database'], cursorclass=cursors.Cursor)
        c = db.cursor()
        c.execute("""SELECT DISTINCT xp_admin from mushcode_experience""")
        source_tuple = c.fetchall()
        c.execute("""SELECT DISTINCT xp_objid from mushcode_experience""")
        char_tuple = c.fetchall()
        source_check = {source: pmatch(source) for source in [field[0] for field in source_tuple] if pmatch(source)}
        char_check = {char: pmatch(char) for char in [field[0] for field in char_tuple] if pmatch(char)}
        kind_dict = {'XP': 'xp', 'SOLXP': 'solar_xp', 'WHIXP': 'white_xp', 'SILXP': 'silver_xp', 'GOLXP': 'gold_xp'}
        game = Game.objects.filter(key='ex3').first()
        kind_models = {}
        for k, v in kind_dict.iteritems():
            kind, created = game.experiences.get_or_create(key=v)
            kind_models[k] = kind
        db.close()
        db = MySQLdb.connect(host=sql_dict['site'], user=sql_dict['username'],
                             passwd=sql_dict['password'], db=sql_dict['database'], cursorclass=cursors.DictCursor)
        c = db.cursor()
        for k, v in char_check.iteritems():
            c.execute("""SELECT * from mushcode_experience WHERE xp_objid=%s""", (k,))
            sql_results = c.fetchall()
            for row in sql_results:
                source = source_check.get(row['xp_admin'], None)
                if source:
                    source = source.stub
                date = row['xp_date'].replace(tzinfo=pytz.utc)
                reason = row['xp_reason']
                type = kind_models[row['xp_type']]
                amount = row['xp_amount']
                link, created = type.exp_links.get_or_create(character=v.storyteller)
                new_xp = link.entries.create(amount=amount, reason=reason, source=source, date_awarded=date)
                new_xp.save()
        db.close()

    def switch_jobs(self):

        # Step one is importing all of the Job Categories from the MUSH data. Each category is a THING object
        # So we don't need mysql just yet.
        cat_dict = dict()
        old_categories = cobj('jobdb').children.all()
        for old_cat in old_categories:
            anon = old_cat.mushget('ANONYMOUS') or 0
            desc = old_cat.mushget('DESCRIBE') or None
            if desc:
                desc = desc.decode('utf-8', errors='ignore')
                desc = process_penntext(desc)
            due = duration_from_string('7d')
            new_cat, created = JobCategory.objects.get_or_create(key=old_cat.name, anonymous=anon, description=desc,
                                                                 due=due)
            if created:
                new_cat.setup()
            cat_dict[old_cat.objid] = new_cat

        # Establishing Mysql Connection!
        from commands.mysql import sql_dict
        db = MySQLdb.connect(host=sql_dict['site'], user=sql_dict['username'],
                             passwd=sql_dict['password'], db=sql_dict['database'], cursorclass=cursors.DictCursor)
        c = db.cursor()

        # Our next order of business is retrieving all of the players who've ever posted jobs.
        # This section searches the database by OBJID and creates a dictionary that links the old jobsys player_id
        # to the new communications.ObjectStub, creating them if necessary.
        c.execute("""SELECT * from jobsys_players""")
        old_players = c.fetchall()
        char_dict = dict()
        for old_player in old_players:
            match = objmatch(old_player['objid'])
            if match:
                char = match.obj
            else:
                key = old_player['player_name']
                char = create.create_object(typeclass=settings.BASE_CHARACTER_TYPECLASS, key=key)
                char.config.model.enabled = False
                char.config.model.save(update_fields=['enabled'])
                objid = old_player['objid']
                dbref, csecs = objid.split(':', 1)
                cdate = from_unixtimestring(csecs)
                MushObject.objects.create(objid=objid, dbref=dbref, created=cdate, type=8, recreated=True, obj=char)
            char_dict[old_player['player_id']] = char

        # Now that we have the Player ID->Stub dictionary, we can begin the process of actually importing job data!
        # we only want the jobs from categories that actually exist. Probably rare that any of them wouldn't be, but
        # just in case...
        cat_list = ', '.join("'%s'" % cat for cat in cat_dict.keys())
        c.execute("""SELECT * from jobsys_jobs WHERE job_objid IN (%s) ORDER BY job_id""" % cat_list)
        old_jobs = c.fetchall()
        for row in old_jobs:
            job_id = row['job_id']
            if row['close_date']:
                close_date = row['close_date'].replace(tzinfo=pytz.utc)
            else:
                close_date = None
            if row['due_date']:
                due_date = row['due_date'].replace(tzinfo=pytz.utc)
            else:
                due_date = None
            if row['submit_date']:
                submit_date = row['submit_date'].replace(tzinfo=pytz.utc)
            else:
                submit_date = None
            title = row['job_title']
            if title:
                title = process_penntext(title.decode('utf-8', errors='ignore'))
            status = row['job_status']
            owner = char_dict[row['player_id']]
            text = row['job_text']
            if text:
                text = process_penntext(text.decode('utf-8', errors='ignore'))
            category = cat_dict[row['job_objid']]

            handler_dict = dict()
            # We have our job row data prepped! Now to create the job and its opening comment as well as the owner-handler.
            new_job = category.jobs.create(title=title, submit_date=submit_date, due_date=due_date,
                                           close_date=close_date, status=status)
            new_owner = new_job.characters.create(character=owner, is_owner=True)
            new_owner.comments.create(text=text, date_made=submit_date, comment_mode=0)
            handler_dict[row['player_id']] = new_owner

            # Here it's time to import all of the job's claims, handlers, watchers, and create JobHandler rows for them.
            c.execute("""SELECT * from jobsys_claim WHERE job_id=%s""", (job_id,))
            claim_data = c.fetchall()
            for old_claim in claim_data:
                new_handler, created = new_job.characters.get_or_create(character=char_dict[old_claim['player_id']])
                if old_claim['claim_mode'] == 0:
                    new_handler.is_handler = True
                if old_claim['claim_mode'] == 1:
                    new_handler.is_helper = True
                new_handler.save()
                handler_dict[old_claim['player_id']] = new_handler

            # Unfortunately it's also possible that people who didn't claim it might also need JobHandler entries so...
            c.execute("""SELECT DISTINCT player_id from jobsys_comments WHERE job_id=%s""", (job_id,))
            all_speakers = c.fetchall()
            for speaker in all_speakers:
                if speaker['player_id'] not in handler_dict:
                    new_handler, created = new_job.characters.get_or_create(character=char_dict[speaker['player_id']])
                    handler_dict[speaker['player_id']] = new_handler

            # And another round. This time it's a matter of importing handlers for anyone who ever CHECKED a job.
            # Here we'll also import everyone's 'last date they checked the job'.
            c.execute("""SELECT * FROM jobsys_check WHERE job_id=%s""", (job_id,))
            old_checks = c.fetchall()
            for check in old_checks:
                if check['player_id'] not in handler_dict:
                    handler, created = new_job.characters.get_or_create(character=char_dict[check['player_id']])
                    handler_dict[check['player_id']] = new_handler
                else:
                    handler = handler_dict[check['player_id']]
                handler.check_date = check['check_date'].replace(tzinfo=pytz.utc)
                handler.save(update_fields=['check_date'])

            # Now to import all of the comments and replies.
            c.execute("""SELECT * from jobsys_comments WHERE job_id=%s ORDER BY comment_id""", (job_id,))
            old_comments = c.fetchall()
            for old_com in old_comments:
                handler = handler_dict[old_com['player_id']]
                comment_text = old_com['comment_text']
                if comment_text:
                    comment_text = process_penntext(comment_text.decode('utf-8', errors='ignore'))
                comment_date = old_com['comment_date'].replace(tzinfo=pytz.utc)
                private = old_com['comment_type']
                if private:
                    mode = 2
                else:
                    mode = 1
                handler.comments.create(text=comment_text, date_made=comment_date, is_private=private,
                                        comment_mode=mode)
        db.close()

    def switch_scenes(self):

        # Establishing Mysql Connection!
        from commands.mysql import sql_dict
        db = MySQLdb.connect(host=sql_dict['site'], user=sql_dict['username'],
                             passwd=sql_dict['password'], db=sql_dict['database'], cursorclass=cursors.DictCursor)
        c = db.cursor()

        # Just like with jobs, we need to create Stubs for everyone who has ever used SceneSys and link them to their
        # Scene IDs! Same code, believe it or not.
        c.execute("""SELECT * from scene_players""")
        old_players = c.fetchall()
        char_dict = dict()
        for old_player in old_players:
            match = objmatch(old_player['objid'])
            if match:
                char = match.obj
            else:
                key = old_player['player_name']
                char = create.create_object(typeclass=settings.BASE_CHARACTER_TYPECLASS, key=key)
                char.config.model.enabled = False
                char.config.model.save(update_fields=['enabled'])
                objid = old_player['objid']
                dbref, csecs = objid.split(':', 1)
                cdate = from_unixtimestring(csecs)
                new_mush = MushObject.objects.create(objid=objid, dbref=dbref, created=cdate, type=8, recreated=1, obj=char)
                new_mush.save()
            char_dict[old_player['player_id']] = char

        # Convert plots! This one's pretty easy.
        c.execute("""SELECT * FROM scene_plots ORDER BY plot_id""")
        old_plots = c.fetchall()
        plot_dict = dict()
        for old_plot in old_plots:
            if old_plot['start_date']:
                start_date = old_plot['start_date'].replace(tzinfo=pytz.utc)
            else:
                start_date = None
            if old_plot['end_date']:
                end_date = old_plot['end_date'].replace(tzinfo=pytz.utc)
            else:
                end_date = None
            owner = char_dict[old_plot['player_id']]
            description = old_plot['plot_desc']
            if description:
                description = process_penntext(description.decode('utf-8', errors='ignore'))
            plot_type = old_plot['plot_type']
            title = old_plot['plot_title']
            if title:
                title = process_penntext(old_plot['plot_title'].decode('utf-8', errors='ignore'))
            new_plot = Plot.objects.create(description=description, title=title, date_start=start_date,
                                date_end=end_date, type=plot_type)
            new_plot.runners.create(character=owner, owner=True)
            plot_dict[old_plot['plot_id']]= new_plot

        # Now we begin the process of importing scenes. This is a very involved process!
        scene_dict = dict()
        source_dict = dict()
        c.execute("""SELECT * FROM scene_scenes ORDER BY scene_id""")
        old_scenes = c.fetchall()
        for old_scene in old_scenes:
            owner = char_dict[old_scene['player_id']]
            scene_title = old_scene['scene_title']
            if scene_title:
                scene_title = process_penntext(scene_title.decode('utf-8', errors='ignore'))
            scene_desc = old_scene['scene_desc']
            if scene_desc:
                scene_desc = process_penntext(scene_desc.decode('utf-8', errors='ignore'))
            scene_status = int(old_scene['scene_state'])

            creation_date = old_scene['creation_date'].replace(tzinfo=pytz.utc)

            if old_scene['finish_date']:
                finish_date = old_scene['finish_date'].replace(tzinfo=pytz.utc)
            else:
                finish_date = None

            plot = plot_dict.get(old_scene['plot_id'], None)
            room_objid = old_scene['room_objid']
            room_name = old_scene['room_name']
            old_loc = objmatch(room_objid)
            if old_loc.obj:
                location = old_loc.obj
            else:
                location = None
            source, scr = Source.objects.get_or_create(key=room_name, location=location)

            new_scene = Event.objects.create(title=scene_title, outcome=scene_desc, status=scene_status,
                                             date_created=creation_date, date_started=creation_date,
                                             date_finished=finish_date, plot=plot)
            new_scene.participants.create(character=owner, owner=True)
            scene_dict[old_scene['scene_id']] = new_scene

            # In this section we'll be setting up the Participants for this scene and making an index dictionary
            # in preparation to import the poses.
            part_dict = dict()
            c.execute("""SELECT DISTINCT player_id FROM scene_poses WHERE scene_id=%s""", (old_scene['scene_id'],))
            posers = c.fetchall()
            for poser in posers:
                new_part, pcr = new_scene.participants.get_or_create(character=char_dict[poser['player_id']])
                part_dict[poser['player_id']] = new_part

            # Finally it's time to import the individual poses!
            pose_dict = dict()
            c.execute("""SELECT * from scene_poses WHERE scene_id=%s""", (old_scene['scene_id'],))
            old_poses = c.fetchall()
            for pose in old_poses:
                parse_pose = pose['pose']
                if parse_pose:
                    parse_pose = parse_pose.decode('utf-8', errors='ignore')
                owner = part_dict[pose['player_id']]
                pose_date = pose['pose_time'].replace(tzinfo=pytz.utc)
                ignore = bool(int(pose['pose_ignore']))
                pose_text = process_penntext(parse_pose)

                new_pose = new_scene.actions.create(owner=owner, ignore=ignore, text=pose_text, date_made=pose_date,
                                                    source=source)
                pose_dict[pose['pose_id']] = new_pose

            # Last stage. We'll update any pairings if need be.
            pair_dict = dict()
            c.execute("""SELECT * from scene_pairs WHERE scene_id=%s""", (old_scene['scene_id'],))
            old_pairs = c.fetchall()
            for old_pair in old_pairs:
                pair_id = old_pair['pair_id']
                num = old_pair['pair_num']
                new_pair, pacr = new_scene.pairings.get_or_create(number=num)
                c.execute("""SELECT * from scene_match WHERE pair_id=%s""", (old_pair['pair_id'],))
                old_match = c.fetchall()
                for mat in old_match:
                    char = char_dict[mat['player_id']]
                    new_pair.characters.add(char)


        # Another easy one. Importing the Events calendar of scheduled scenes.
        event_dict = dict()
        c.execute("""SELECT * from scene_schedule ORDER BY schedule_id""")
        old_events = c.fetchall()
        for old_event in old_events:
            owner = char_dict[old_event['player_id']]
            schedule_date = old_event['schedule_date'].replace(tzinfo=pytz.utc)
            creation_date = schedule_date - duration_from_string('4d')
            description = process_penntext(old_event['schedule_desc'])
            schedule_title = process_penntext(old_event['schedule_title'])
            plot = plot_dict.get(old_event['plot_id'], None)

            new_event = Event.objects.create(date_scheduled=schedule_date, pitch=description,
                                                title=schedule_title, plot=plot, date_created=creation_date)
            new_event.participants.create(character=owner, owner=True)
            event_dict[old_event['schedule_id']] = new_event

            c.execute("""SELECT * from scene_tags WHERE schedule_id=%s""", (old_event['schedule_id'],))
            old_tags = c.fetchall()
            for tagger in old_tags:
                tagee = char_dict[tagger['player_id']]
                new_event.participants.get_or_create(character=tagee, tag=True)


        db.close()