# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-07 17:09
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('logins', '0013_auto_20160407_1708'),
    ]

    operations = [
        migrations.AlterField(
            model_name='login',
            name='date',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 7, 17, 9, 1, 955755, tzinfo=utc)),
        ),
    ]
