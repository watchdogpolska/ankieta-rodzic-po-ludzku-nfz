# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-19 09:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0008_auto_20161119_0712'),
    ]

    operations = [
        migrations.AddField(
            model_name='subquestion',
            name='kind',
            field=models.TextField(choices=[('int', 'Integer'), ('text', 'Text'), ('ltext', 'Long text')], default='text', verbose_name='Kind of answer'),
        ),
    ]
