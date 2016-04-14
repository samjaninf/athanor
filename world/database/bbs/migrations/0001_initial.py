# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-13 20:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=40)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('lock_storage', models.TextField(blank=True, verbose_name='locks')),
                ('anonymous', models.CharField(max_length=80, null=True)),
                ('timeout', models.DurationField(null=True)),
                ('mandatory', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='BoardGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main', models.BooleanField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creation_date', models.DateTimeField(null=True)),
                ('timeout_date', models.DateTimeField(null=True)),
                ('modify_date', models.DateTimeField(null=True)),
                ('text', models.TextField(blank=True)),
                ('subject', models.CharField(max_length=30)),
                ('timeout', models.DurationField(null=True)),
                ('remaining_timeout', models.FloatField(null=True)),
                ('order', models.PositiveSmallIntegerField(null=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='bbs.Board')),
            ],
        ),
    ]
