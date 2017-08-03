# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields
import edxval.models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0005_videoimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transcript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('video_id', models.CharField(max_length=255)),
                ('transcript', edxval.models.CustomizableFileField(null=True, blank=True)),
                ('language', models.CharField(max_length=8, db_index=True)),
                ('provider', models.CharField(default=b'Custom', max_length=30, choices=[(b'Custom', b'Custom'), (b'3PlayMedia', b'3PlayMedia'), (b'Cielo24', b'Cielo24')])),
                ('fmt', models.CharField(db_index=True, max_length=20, choices=[(b'srt', b'SubRip'), (b'sjson', b'SRT JSON')])),
            ],
        ),
        migrations.RemoveField(
            model_name='subtitle',
            name='video',
        ),
        migrations.DeleteModel(
            name='Subtitle',
        ),
        migrations.AlterUniqueTogether(
            name='transcript',
            unique_together=set([('video_id', 'language')]),
        ),
    ]
