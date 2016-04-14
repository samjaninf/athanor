# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-13 20:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('objects', '0005_auto_20150403_2339'),
        ('comms', '0007_msg_db_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=60, unique=True)),
                ('order', models.IntegerField(default=0)),
                ('tier', models.PositiveSmallIntegerField(default=1)),
                ('lock_storage', models.TextField(blank=True, verbose_name='locks')),
                ('abbreviation', models.CharField(max_length=10)),
                ('color', models.CharField(max_length=20, null=True)),
                ('description', models.TextField(blank=True)),
                ('ic_enabled', models.BooleanField(default=True)),
                ('ooc_enabled', models.BooleanField(default=True)),
                ('display_type', models.SmallIntegerField(default=0)),
                ('timeout', models.DurationField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=120, null=True)),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='objects.ObjectDB')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='groups.Group')),
            ],
        ),
        migrations.CreateModel(
            name='GroupPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=12, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupRank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.IntegerField(default=0)),
                ('name', models.CharField(max_length=35)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ranks', to='groups.Group')),
                ('permissions', models.ManyToManyField(to='groups.GroupPermissions')),
            ],
        ),
        migrations.AddField(
            model_name='groupparticipant',
            name='permissions',
            field=models.ManyToManyField(to='groups.GroupPermissions'),
        ),
        migrations.AddField(
            model_name='groupparticipant',
            name='rank',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='holders', to='groups.GroupRank'),
        ),
        migrations.AddField(
            model_name='group',
            name='alert_rank',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.GroupRank'),
        ),
        migrations.AddField(
            model_name='group',
            name='guest_permissions',
            field=models.ManyToManyField(to='groups.GroupPermissions'),
        ),
        migrations.AddField(
            model_name='group',
            name='ic_channel',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group', to='comms.ChannelDB'),
        ),
        migrations.AddField(
            model_name='group',
            name='invites',
            field=models.ManyToManyField(related_name='group_invites', to='objects.ObjectDB'),
        ),
        migrations.AddField(
            model_name='group',
            name='member_permissions',
            field=models.ManyToManyField(to='groups.GroupPermissions'),
        ),
        migrations.AddField(
            model_name='group',
            name='ooc_channel',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group', to='comms.ChannelDB'),
        ),
        migrations.AddField(
            model_name='group',
            name='start_rank',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='groups.GroupRank'),
        ),
        migrations.AlterUniqueTogether(
            name='grouprank',
            unique_together=set([('name', 'group'), ('num', 'group')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupparticipant',
            unique_together=set([('character', 'group')]),
        ),
    ]
