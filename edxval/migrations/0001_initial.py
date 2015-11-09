# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import edxval.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CourseVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', models.CharField(max_length=255)),
            ],
            bases=(models.Model, edxval.models.ModelFactoryWithValidation),
        ),
        migrations.CreateModel(
            name='EncodedVideo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('url', models.CharField(max_length=200)),
                ('file_size', models.PositiveIntegerField()),
                ('bitrate', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('profile_name', models.CharField(unique=True, max_length=50, validators=[django.core.validators.RegexValidator(regex=b'^[a-zA-Z0-9\\-_]*$', message=b'profile_name has invalid characters', code=b'invalid profile_name')])),
            ],
        ),
        migrations.CreateModel(
            name='Subtitle',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('fmt', models.CharField(db_index=True, max_length=20, choices=[(b'srt', b'SubRip'), (b'sjson', b'SRT JSON')])),
                ('language', models.CharField(max_length=8, db_index=True)),
                ('content', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('edx_video_id', models.CharField(unique=True, max_length=100, validators=[django.core.validators.RegexValidator(regex=b'^[a-zA-Z0-9\\-_]*$', message=b'edx_video_id has invalid characters', code=b'invalid edx_video_id')])),
                ('client_video_id', models.CharField(db_index=True, max_length=255, blank=True)),
                ('duration', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('status', models.CharField(max_length=255, db_index=True)),
            ],
        ),
        migrations.AddField(
            model_name='subtitle',
            name='video',
            field=models.ForeignKey(related_name='subtitles', to='edxval.Video'),
        ),
        migrations.AddField(
            model_name='encodedvideo',
            name='profile',
            field=models.ForeignKey(related_name='+', to='edxval.Profile'),
        ),
        migrations.AddField(
            model_name='encodedvideo',
            name='video',
            field=models.ForeignKey(related_name='encoded_videos', to='edxval.Video'),
        ),
        migrations.AddField(
            model_name='coursevideo',
            name='video',
            field=models.ForeignKey(related_name='courses', to='edxval.Video'),
        ),
        migrations.AlterUniqueTogether(
            name='coursevideo',
            unique_together=set([('course_id', 'video')]),
        ),
    ]
