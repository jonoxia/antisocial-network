# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gallery',
            name='publicity',
            field=models.CharField(default='PRI', max_length=3, choices=[('PRI', 'Private'), ('FRO', 'Friends-Only'), ('PUB', 'public')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='work',
            name='publicity',
            field=models.CharField(default='PRI', max_length=3, choices=[('PRI', 'Private'), ('FRO', 'Friends-Only'), ('PUB', 'public')]),
            preserve_default=True,
        ),
    ]
