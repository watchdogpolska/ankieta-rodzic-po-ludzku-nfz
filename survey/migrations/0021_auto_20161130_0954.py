# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-30 09:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0020_auto_20161128_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='hospital',
            name='city',
            field=models.CharField(default='', max_length=100, verbose_name='City'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='hospital',
            name='voivodeship',
            field=models.CharField(default='', max_length=100, verbose_name='Voivodeship'),
            preserve_default=False,
        ),
    ]
