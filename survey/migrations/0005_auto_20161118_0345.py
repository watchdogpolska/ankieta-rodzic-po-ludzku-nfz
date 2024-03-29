# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 03:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0004_auto_20161118_0319'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participant',
            name='hospital',
        ),
        migrations.AddField(
            model_name='participant',
            name='health_fund',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='survey.NationalHealtFund'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='survey',
            name='participants',
            field=models.ManyToManyField(through='survey.Participant', to='survey.NationalHealtFund'),
        ),
    ]
