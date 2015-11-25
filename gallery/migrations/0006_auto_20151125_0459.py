# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_auto_20151002_0620'),
    ]

    operations = [
        migrations.AddField(
            model_name='gallery',
            name='urlname',
            field=models.TextField(default='nevermind'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='work',
            name='urlname',
            field=models.TextField(default='nevermind'),
            preserve_default=False,
        ),
    ]
