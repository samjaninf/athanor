# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-12 01:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('objects', '0005_auto_20150403_2339'),
        ('communications', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('date_schedule', models.DateTimeField(db_index=True)),
                ('interest', models.ManyToManyField(to='objects.ObjectDB')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='communications.ObjectStub')),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scenes', to='communications.ObjectStub')),
            ],
        ),
        migrations.CreateModel(
            name='Plot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('date_start', models.DateTimeField(null=True)),
                ('date_end', models.DateTimeField(null=True)),
                ('status', models.SmallIntegerField(db_index=True, default=0)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plots', to='communications.ObjectStub')),
            ],
        ),
        migrations.CreateModel(
            name='Pose',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ignore', models.BooleanField(db_index=True, default=False)),
                ('date_made', models.DateTimeField()),
                ('text', models.TextField(blank=True)),
                ('location', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poses_here', to='communications.ObjectStub')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poses', to='scenes.Participant')),
            ],
        ),
        migrations.CreateModel(
            name='Scene',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150)),
                ('description', models.TextField(blank=True)),
                ('date_created', models.DateTimeField()),
                ('date_finished', models.DateTimeField(null=True)),
                ('status', models.SmallIntegerField(db_index=True, default=0)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scenes', to='communications.ObjectStub')),
                ('plot', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='scenes', to='scenes.Plot')),
            ],
        ),
        migrations.AddField(
            model_name='participant',
            name='scene',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='scenes.Scene'),
        ),
        migrations.AddField(
            model_name='event',
            name='plot',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='scenes.Plot'),
        ),
        migrations.AlterUniqueTogether(
            name='participant',
            unique_together=set([('actor', 'scene')]),
        ),
    ]
