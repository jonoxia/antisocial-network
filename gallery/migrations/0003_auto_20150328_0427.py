# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_auto_20150328_0422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gallery',
            name='publicity',
            field=models.CharField(default=b'PRI', max_length=3, choices=[(b'PRI', b'Private'), (b'FRO', b'Friends-Only'), (b'PUB', b'Public')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='work',
            name='publicity',
            field=models.CharField(default=b'PRI', max_length=3, choices=[(b'PRI', b'Private'), (b'FRO', b'Friends-Only'), (b'PUB', b'Public')]),
            preserve_default=True,
        ),
    ]
