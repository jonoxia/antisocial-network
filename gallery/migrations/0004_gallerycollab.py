# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_auto_20150328_0427'),
    ]

    operations = [
        migrations.CreateModel(
            name='GalleryCollab',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permissions', models.IntegerField()),
                ('publicity', models.CharField(default=b'PRI', max_length=3, choices=[(b'PRI', b'Private'), (b'FRO', b'Friends-Only'), (b'PUB', b'Public')])),
                ('gallery', models.ForeignKey(to='gallery.Gallery')),
                ('person', models.ForeignKey(to='gallery.Human')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
