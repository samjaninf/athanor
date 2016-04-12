# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-12 01:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('objects', '0005_auto_20150403_2339'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('groups', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MushAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objids', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='MushAttribute',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('value', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MushGroupMemberships',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='MushGroupRanks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num', models.PositiveSmallIntegerField()),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='MushObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dbref', models.CharField(db_index=True, max_length=15, unique=True)),
                ('objid', models.CharField(db_index=True, max_length=30, unique=True)),
                ('type', models.PositiveSmallIntegerField(db_index=True)),
                ('name', models.CharField(max_length=80)),
                ('created', models.DateTimeField()),
                ('flags', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MushGroups',
            fields=[
                ('dbref', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='mushgroup', serialize=False, to='mushimport.MushObject')),
                ('group', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mushgroup', to='groups.Group')),
            ],
        ),
        migrations.AddField(
            model_name='mushobject',
            name='destination',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exits_to', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushobject',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushobject',
            name='obj',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mush', to='objects.ObjectDB'),
        ),
        migrations.AddField(
            model_name='mushobject',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='owned', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushobject',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushgroupmemberships',
            name='char',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushgroupmemberships',
            name='rank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='holders', to='mushimport.MushGroupRanks'),
        ),
        migrations.AddField(
            model_name='mushattribute',
            name='dbref',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attrs', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushaccount',
            name='characters',
            field=models.ManyToManyField(to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushaccount',
            name='dbref',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mush_account', to='mushimport.MushObject'),
        ),
        migrations.AddField(
            model_name='mushaccount',
            name='player',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mush_account', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mushgroupranks',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ranks', to='mushimport.MushGroups'),
        ),
        migrations.AddField(
            model_name='mushgroupmemberships',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='members', to='mushimport.MushGroups'),
        ),
        migrations.AlterUniqueTogether(
            name='mushattribute',
            unique_together=set([('dbref', 'name')]),
        ),
    ]
