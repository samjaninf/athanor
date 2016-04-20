# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-19 06:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('objects', '0005_auto_20150403_2339'),
    ]

    operations = [
        migrations.CreateModel(
            name='InfoFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=30)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(null=True)),
                ('text', models.TextField()),
                ('date_approved', models.DateTimeField(null=True)),
                ('approved', models.BooleanField(default=False)),
                ('approved_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='objects.ObjectDB')),
            ],
        ),
        migrations.CreateModel(
            name='InfoType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(db_index=True, default='INFO', max_length=30)),
                ('character_obj', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='infotypes', to='objects.ObjectDB')),
            ],
        ),
        migrations.AddField(
            model_name='infofile',
            name='info_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='info.InfoType'),
        ),
        migrations.AddField(
            model_name='infofile',
            name='set_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='objects.ObjectDB'),
        ),
    ]
