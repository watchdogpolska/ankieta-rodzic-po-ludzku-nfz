# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-27 02:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0013_participant_answer_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='subquestion_count',
            field=models.IntegerField(default=0, verbose_name='Total number of subquestion'),
        ),

    ]
