# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 09:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0009_auto_20170212_1050'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fill',
            name='order',
        ),
    ]