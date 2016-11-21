# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-21 14:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0011_auto_20161121_0017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nationalhealtfund',
            name='email',
            field=models.EmailField(help_text='E-mail to a branch of the national health fund', max_length=254, verbose_name='E-mail'),
        ),
        migrations.AlterField(
            model_name='nationalhealtfund',
            name='identifier',
            field=models.CharField(help_text='ID data to an external computer system', max_length=15, verbose_name='Identifier'),
        ),
        migrations.AlterField(
            model_name='nationalhealtfund',
            name='name',
            field=models.CharField(help_text='Branch name', max_length=150, verbose_name='Name'),
        ),
    ]
