# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-07 18:27
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0014_auto_20160407_1709'),
    ]

    operations = [
        migrations.AlterField(
            model_name='infofile',
            name='date_created',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 7, 18, 27, 50, 131716, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='infofile',
            name='date_modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 4, 7, 18, 27, 50, 131735, tzinfo=utc)),
        ),
    ]
