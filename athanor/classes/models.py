from django.db import models
from evennia.typeclasses.models import SharedMemoryModel
from athanor.utils.time import utcnow


class Host(models.Model):
    address = models.IPAddressField(unique=True, null=False)
    hostname = models.TextField(null=True)
    date_created = models.DateTimeField(null=True)
    date_updated = models.DateTimeField(null=True)


class LoginRecord(models.Model):
    account = models.ForeignKey('accounts.AccountDB', related_name='login_records', on_delete=models.PROTECT)
    host = models.ForeignKey(Host, related_name='logins', on_delete=models.PROTECT)
    date_created = models.DateTimeField(null=False)
    result = models.PositiveSmallIntegerField(default=0)


class CharacterBridge(SharedMemoryModel):
    db_object = models.OneToOneField('objects.ObjectDB', related_name='character_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False)
    db_account = models.ForeignKey('accounts.AccountDB', related_name='owned_characters', on_delete=models.SET_NULL,
                                   null=True)
    db_namespace = models.IntegerField(default=0, null=True)

    class Meta:
        verbose_name = 'Character'
        verbose_name_plural = 'Characters'
        unique_together = (('db_namespace', 'db_iname'),)


class StructureBridge(SharedMemoryModel):
    db_object = models.OneToOneField('objects.ObjectDB', related_name='structure_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_structure_path = models.CharField(max_length=255, null=False, blank=False)
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False, unique=True)


class RegionBridge(models.Model):
    object = models.OneToOneField('objects.ObjectDB', related_name='region_bridge', primary_key=True,
                                  on_delete=models.CASCADE)
    system_key = models.CharField(max_length=255, blank=False, null=False, unique=True)


class InstanceBridge(models.Model):
    object = models.OneToOneField('objects.ObjectDB', related_name='instance_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    extension = models.CharField(max_length=255, null=False, blank=False)
    instance_key = models.CharField(max_length=255, null=False, blank=False)


class GameLocations(models.Model):
    object = models.ForeignKey('objects.ObjectDB', related_name='saved_locations', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=False, blank=False)
    instance = models.ForeignKey('objects.ObjectDB', related_name='objects_here', on_delete=models.CASCADE)
    room_key = models.CharField(max_length=255, null=False, blank=False)
    x_coordinate = models.FloatField(null=True)
    y_coordinate = models.FloatField(null=True)
    z_coordinate = models.FloatField(null=True)

    class Meta:
        unique_together = (('object', 'name'),)


class Mail(SharedMemoryModel):
    db_subject = models.TextField(null=False, blank=False)
    db_body = models.TextField(null=False, blank=False)

    class Meta:
        verbose_name = 'Mail'
        verbose_name_plural = 'Mail'


class MailLink(SharedMemoryModel):
    db_mail = models.ForeignKey('mail.Mail', related_name='mail_links', on_delete=models.CASCADE)
    db_owner = models.ForeignKey('objects.ObjectDB', related_name='mail_links', on_delete=models.CASCADE)
    db_link_type = models.PositiveSmallIntegerField(default=0)
    db_link_active = models.BooleanField(default=True)
    db_date_read = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'MailLink'
        verbose_name_plural = 'MailLinks'
        unique_together = (('db_mail', 'db_owner'),)
        index_together = (('db_owner', 'db_link_active', 'db_link_type'),)


class Note(SharedMemoryModel):
    db_object = models.ForeignKey('objects.ObjectDB', related_name='notes', on_delete=models.CASCADE)
    db_category = models.CharField(max_length=255, null=False, blank=False)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False)
    db_contents = models.TextField(blank=False, null=False)
    db_date_created = models.DateTimeField(null=False)
    db_date_modified = models.DateTimeField(null=False)
    db_approved_by = models.ForeignKey('objects.ObjectDB', related_name='approved_notes', on_delete=models.PROTECT, null=True)

    class Meta:
        unique_together = (('db_object', 'db_category', 'db_iname'),)
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'



class AllianceBridge(SharedMemoryModel):
    db_object = models.OneToOneField('objects.ObjectDB', related_name='alliance_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False, unique=True)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_abbreviation = models.CharField(max_length=20, null=True, blank=False)
    db_iabbreviation = models.CharField(max_length=20, null=True, blank=False, unique=True)
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False, unique=True)


class FactionBridge(SharedMemoryModel):
    db_object = models.OneToOneField('objects.ObjectDB', related_name='faction_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_alliance = models.ForeignKey(AllianceBridge, related_name='factions', on_delete=models.PROTECT, null=True)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False, unique=True)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_abbreviation = models.CharField(max_length=20, null=True, blank=False)
    db_iabbreviation = models.CharField(max_length=20, null=True, blank=False, unique=True)
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False, unique=True)

    class Meta:
        verbose_name = 'Faction'
        verbose_name_plural = 'Factions'


class DivisionBridge(SharedMemoryModel):
    db_object = models.OneToOneField('objects.ObjectDB', related_name='division_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_faction = models.ForeignKey(FactionBridge, related_name='divisions', on_delete=models.PROTECT)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_system_identifier = models.CharField(max_length=255, null=True, blank=False, unique=True)

    class Meta:
        unique_together = (('db_faction', 'db_iname'),)
        verbose_name = 'Division'
        verbose_name_plural = 'Divisions'


class ForumCategoryBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='forum_category_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, blank=False, null=False)
    db_iname = models.CharField(max_length=255, blank=False, null=False, unique=True)
    db_cname = models.CharField(max_length=255, blank=False, null=False)
    db_abbr = models.CharField(max_length=5, blank=True, null=False)
    db_iabbr = models.CharField(max_length=5, unique=True, blank=True, null=False)
    db_cabbr = models.CharField(max_length=50, blank=False, null=False)

    class Meta:
        verbose_name = 'ForumCategory'
        verbose_name_plural = 'ForumCategories'

    def __str__(self):
        return str(self.db_name)


class ForumBoardBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='forum_board_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_category = models.ForeignKey(ForumCategoryBridge, related_name='boards', null=False, on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, blank=False, null=False)
    db_iname = models.CharField(max_length=255, blank=False, null=False)
    db_cname = models.CharField(max_length=255, blank=False, null=False)
    db_order = models.PositiveIntegerField(default=0)
    ignore_list = models.ManyToManyField('objects.ObjectDB')
    db_mandatory = models.BooleanField(default=False)

    def __str__(self):
        return str(self.db_name)

    class Meta:
        verbose_name = 'Forum'
        verbose_name_plural = 'Forums'
        unique_together = (('db_category', 'db_order'), ('db_category', 'db_iname'))


class ForumThreadBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='forum_thread_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_account = models.ForeignKey('accounts.AccountDB', related_name='+', null=True,
                                   on_delete=models.SET_NULL)
    db_object = models.ForeignKey('objects.ObjectDB', related_name='+', null=True, on_delete=models.SET_NULL)
    db_name = models.CharField(max_length=255, blank=False, null=False)
    db_iname = models.CharField(max_length=255, blank=False, null=False)
    db_cname = models.CharField(max_length=255, blank=False, null=False)
    db_date_created = models.DateTimeField(null=False)
    db_board = models.ForeignKey(ForumBoardBridge, related_name='threads', on_delete=models.CASCADE)
    db_date_modified = models.DateTimeField(null=False)
    db_order = models.PositiveIntegerField(null=True)

    class Meta:
        verbose_name = 'Thread'
        verbose_name_plural = 'Threads'
        unique_together = (('db_board', 'db_order'), ('db_board', 'db_iname'))

    @classmethod
    def validate_key(cls, key_text, rename_from=None):
        return key_text

    @classmethod
    def validate_order(cls, order_text, rename_from=None):
        return int(order_text)

    @classmethod
    def create(cls, *args, **kwargs):
        board = kwargs.get('board', None)
        if not isinstance(board, ForumThreadBridge):
            raise ValueError("Posts must be linked to a board!")

        owner = kwargs.get('owner', None)
        key = kwargs.get('key', None)
        key = cls.validate_key(key)

        text = kwargs.get('text', None)
        if not text:
            raise ValueError("Post body is empty!")

        order = kwargs.get('order', None)
        if order:
            order = cls.validate_order(order)
        else:
            last_post = board.last_post()
            if last_post:
                order = last_post.order + 1
            else:
                order = 1

        new_post = cls(db_key=key, db_order=order, db_board=board, db_owner=owner, db_text=text)
        new_post.save()
        return new_post

    def __str__(self):
        return self.subject

    def post_alias(self):
        return f"{self.board.alias}/{self.order}"

    def can_edit(self, checker=None):
        if self.owner.account_stub.account == checker:
            return True
        return self.board.check_permission(checker=checker, type="admin")

    def edit_post(self, find=None, replace=None):
        if not find:
            raise ValueError("No text entered to find.")
        if not replace:
            replace = ''
        self.date_modified = utcnow()
        self.text = self.text.replace(find, replace)

    def update_read(self, account):
        acc_read, created = self.read.get_or_create(account=account)
        acc_read.date_read = utcnow()
        acc_read.save()


class ForumThreadRead(models.Model):
    account = models.ForeignKey('accounts.AccountDB', related_name='forum_read', on_delete=models.CASCADE)
    thread = models.ForeignKey(ForumThreadBridge, related_name='read', on_delete=models.CASCADE)
    date_read = models.DateTimeField(null=True)

    class Meta:
        unique_together = (('account', 'thread'),)


class ForumPost(models.Model):
    account = models.ForeignKey('accounts.AccountDB', related_name='+', null=True, on_delete=models.SET_NULL)
    object = models.ForeignKey('objects.ObjectDB', related_name='+', null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(null=False)
    thread = models.ForeignKey(ForumThreadBridge, related_name='posts', on_delete=models.CASCADE)
    date_modified = models.DateTimeField(null=False)
    order = models.PositiveIntegerField(null=True)
    body = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'
        unique_together = (('thread', 'order'), )



class PlotBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='plot_bridge', on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False, unique=True)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_pitch = models.TextField(blank=True, null=True)
    db_summary = models.TextField(blank=True, null=True)
    db_outcome = models.TextField(blank=True, null=True)
    db_date_start = models.DateTimeField(null=True)
    db_date_end = models.DateTimeField(null=True)

    class Meta:
        verbose_name = 'Plot'
        verbose_name_plural = 'Plots'


class PlotRunner(SharedMemoryModel):
    db_plot = models.ForeignKey(PlotBridge, related_name='runners', on_delete=models.CASCADE)
    db_object = models.ForeignKey('objects.ObjectDB', related_name='plots', on_delete=models.PROTECT)
    db_runner_type = models.PositiveSmallIntegerField(default=0)
    # Runner type 0: Low level. 1: Helper. 2: Owner.

    class Meta:
        unique_together = (('db_plot', 'db_object'),)
        index_together = (('db_plot', 'db_runner_type'),)
        verbose_name = 'PlotRunner'
        verbose_name_plural = ' PlotRunners'


class EventBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='event_bridge', on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False, unique=True)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_pitch = models.TextField(blank=True, null=True, default=None)
    db_outcome = models.TextField(blank=True, null=True, default=None)
    db_location = models.TextField(blank=True, null=True, default=None)
    db_date_created = models.DateTimeField(null=True)
    db_date_scheduled = models.DateTimeField(null=True)
    db_date_started = models.DateTimeField(null=True)
    db_date_finished = models.DateTimeField(null=True)
    plots = models.ManyToManyField(PlotBridge, related_name='events')
    db_thread = models.OneToOneField('forum.ForumThreadBridge', related_name='event', null=True, on_delete=models.SET_NULL)
    db_status = models.PositiveSmallIntegerField(default=0, db_index=True)
    # Status: 0 = Active. 1 = Paused. 2 = ???. 3 = Finished. 4 = Scheduled. 5 = Canceled.


class EventParticipant(SharedMemoryModel):
    db_object = models.ForeignKey('objects.ObjectDB', related_name='logs', on_delete=models.PROTECT)
    db_event = models.ForeignKey(EventBridge, related_name='participants', on_delete=models.CASCADE)
    db_participant_type = models.PositiveSmallIntegerField(default=0)
    db_action_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("db_object", "db_event"),)
        index_together = (('db_event', 'db_participant_type'),)
        verbose_name = 'EventParticipant'
        verbose_name_plural = 'EventParticipants'


class EventSource(SharedMemoryModel):
    db_name = models.CharField(max_length=255, null=True, blank=False)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_event = models.ForeignKey(EventBridge, related_name='event_sources', on_delete=models.CASCADE)
    db_source_type = models.PositiveIntegerField(default=0)
    # source type: 0 = 'Location Pose'. 1 = Channel. 2 = room-based OOC

    class Meta:
        unique_together = (('db_event', 'db_source_type', 'db_name'),)
        verbose_name = "EventSource"
        verbose_name_plural = "EventSources"


class EventCodename(SharedMemoryModel):
    db_name = models.CharField(max_length=255, null=True, blank=False)
    db_cname = models.CharField(max_length=255, null=False, blank=False)
    db_participant = models.ForeignKey(EventParticipant, related_name='codenames', on_delete=models.PROTECT)

    class Meta:
        unique_together = (('db_participant', 'db_name'),)
        verbose_name = 'EventCodeName'
        verbose_name_plural = 'EventCodeNames'


class EventAction(SharedMemoryModel):
    db_event = models.ForeignKey(EventBridge, related_name='actions', on_delete=models.CASCADE)
    db_participant = models.ForeignKey(EventParticipant, related_name='actions', on_delete=models.CASCADE)
    db_source = models.ForeignKey(EventSource, related_name='actions', on_delete=models.PROTECT)
    db_ignore = models.BooleanField(default=False, db_index=True)
    db_sort_order = models.PositiveIntegerField(default=0)
    db_text = models.TextField(blank=True)
    db_codename = models.ForeignKey(EventCodename, related_name='actions', null=True, on_delete=models.PROTECT)

    class Meta:
        verbose_name = 'EventAction'
        verbose_name_plural = 'EventActions'


class ThemeBridge(SharedMemoryModel):
    db_script = models.OneToOneField('scripts.ScriptDB', related_name='theme_bridge', primary_key=True,
                                     on_delete=models.CASCADE)
    db_name = models.CharField(max_length=255, null=False, blank=False)
    db_iname = models.CharField(max_length=255, null=False, blank=False, unique=True)
    db_cname = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        verbose_name = 'Theme'
        verbose_name_plural = 'Themes'


class ThemeParticipant(SharedMemoryModel):
    db_theme = models.ForeignKey(ThemeBridge, related_name='participants', on_delete=models.CASCADE)
    db_object = models.ForeignKey('objects.ObjectDB', related_name='themes', on_delete=models.CASCADE)
    db_list_type = models.CharField(max_length=50, blank=False, null=False)

    class Meta:
        unique_together = (('db_theme', 'db_object'),)
        verbose_name = 'ThemeParticipant'
        verbose_name_plural = 'ThemeParticipants'