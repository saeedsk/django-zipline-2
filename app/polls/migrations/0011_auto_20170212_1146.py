# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 09:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0010_remove_fill_order'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='sid',
            new_name='order_sid',
        ),
        migrations.AddField(
            model_name='fill',
            name='fill_sid',
            field=models.CharField(default='-', max_length=20),
        ),
    ]