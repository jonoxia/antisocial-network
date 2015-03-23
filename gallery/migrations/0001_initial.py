# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('when', models.DateTimeField()),
                ('commentText', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('mode', models.TextField()),
                ('startDate', models.DateTimeField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.TextField()),
                ('blurb', models.TextField()),
                ('type', models.TextField()),
                ('theme', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Human',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pictureUrl', models.TextField()),
                ('publicName', models.TextField()),
                ('bio', models.TextField()),
                ('account', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublicitySetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('setting', models.IntegerField()),
                ('conversation', models.ForeignKey(to='gallery.Conversation')),
                ('person', models.ForeignKey(to='gallery.Human')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tagText', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('thumbnailUrl', models.TextField()),
                ('imageUrl', models.TextField()),
                ('sequence_num', models.IntegerField()),
                ('title', models.TextField()),
                ('body', models.TextField()),
                ('workType', models.TextField()),
                ('publishDate', models.DateTimeField()),
                ('modifyDate', models.DateTimeField()),
                ('publicity', models.IntegerField()),
                ('gallery', models.ForeignKey(to='gallery.Gallery')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='tag',
            name='works',
            field=models.ManyToManyField(related_name='tags', to='gallery.Work'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='gallery',
            name='author',
            field=models.ForeignKey(to='gallery.Human'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conversation',
            name='topic',
            field=models.ForeignKey(to='gallery.Work', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='conversation',
            field=models.ForeignKey(to='gallery.Conversation'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='comment',
            name='person',
            field=models.ForeignKey(to='gallery.Human'),
            preserve_default=True,
        ),
    ]
