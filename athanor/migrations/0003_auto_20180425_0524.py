# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-04-25 05:24


import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('athanor', '0002_auto_20180425_0523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountcore',
            name='playtime',
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
        migrations.AlterField(
            model_name='charactercore',
            name='playtime',
            field=models.DurationField(default=datetime.timedelta(0)),
        ),
    ]