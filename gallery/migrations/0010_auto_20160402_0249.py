# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-02 02:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0009_document_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='work',
            name='body',
            field=models.TextField(default=b''),
        ),
    ]
