# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-02 01:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0023_participant_accept_on'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hospital',
            name='city',
        ),
        migrations.RemoveField(
            model_name='hospital',
            name='voivodeship',
        ),
    ]