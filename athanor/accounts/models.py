from django.db import models
from evennia.typeclasses.models import SharedMemoryModel


class AccountBridge(SharedMemoryModel):
    db_account = models.OneToOneField('accounts.AccountDB', related_name='account_bridge', primary_key=True,
                                      on_delete=models.CASCADE)
    db_object = models.OneToOneField('objects.ObjectDB', related_name='account_bridge', on_delete=models.CASCADE)


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
