# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import gallery.models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0007_document'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='work',
            name='imageUrl',
        ),
        migrations.AddField(
            model_name='document',
            name='filetype',
            field=models.CharField(default=b'IMG', max_length=3, choices=[(b'IMG', b'Image'), (b'AUD', b'Audio'), (b'MOV', b'Movie')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='document',
            name='works',
            field=models.ManyToManyField(related_name='documents', to='gallery.Work'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='document',
            name='docfile',
            field=models.FileField(upload_to=gallery.models.user_directory_path),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='work',
            name='title',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
    ]
