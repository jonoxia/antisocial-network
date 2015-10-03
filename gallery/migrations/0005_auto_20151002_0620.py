# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_gallerycollab'),
    ]

    operations = [
        migrations.RenameField(
            model_name='work',
            old_name='sequence_num',
            new_name='sequenceNum',
        ),
        migrations.AlterField(
            model_name='work',
            name='publishDate',
            field=models.DateTimeField(default=None, null=True),
            preserve_default=True,
        ),
    ]
