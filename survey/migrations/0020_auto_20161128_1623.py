# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-28 16:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0019_auto_20161128_1552'),
    ]

    operations = [
        migrations.AlterField(
            model_name='survey',
            name='print_style',
            field=models.IntegerField(choices=[(0, 'Print per hospital'), (1, 'Print per participant')], default=1),
        ),
    ]