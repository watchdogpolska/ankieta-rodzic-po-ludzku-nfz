# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 03:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0002_auto_20161118_0256'),
    ]

    operations = [
        migrations.RenameField(
            model_name='answer',
            old_name='entity',
            new_name='participant',
        ),
    ]
