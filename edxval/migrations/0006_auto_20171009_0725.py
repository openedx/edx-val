# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import model_utils.fields
import django.utils.timezone
import edxval.models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0005_videoimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranscriptPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course_id', models.CharField(unique=True, max_length=255, verbose_name=b'Course ID')),
                ('provider', models.CharField(max_length=20, verbose_name=b'Provider', choices=[(b'Custom', b'Custom'), (b'3PlayMedia', b'3PlayMedia'), (b'Cielo24', b'Cielo24')])),
                ('cielo24_fidelity', models.CharField(blank=True, max_length=20, null=True, verbose_name=b'Cielo24 Fidelity', choices=[(b'MECHANICAL', b'Mechanical, 75% Accuracy'), (b'PREMIUM', b'Premium, 95% Accuracy'), (b'PROFESSIONAL', b'Professional, 99% Accuracy')])),
                ('cielo24_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name=b'Cielo24 Turnaround', choices=[(b'STANDARD', b'Standard, 48h'), (b'PRIORITY', b'Priority, 24h')])),
                ('three_play_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name=b'3PlayMedia Turnaround', choices=[(b'extended_service', b'10-Day/Extended'), (b'default', b'4-Day/Default'), (b'expedited_service', b'2-Day/Expedited'), (b'rush_service', b'24 hour/Rush'), (b'same_day_service', b'Same Day')])),
                ('preferred_languages', edxval.models.ListField(default=[], verbose_name=b'Preferred Languages', max_items=50, blank=True)),
                ('video_source_language', models.CharField(help_text=b'This specifies the speech language of a Video.', max_length=50, null=True, verbose_name=b'Video Source Language', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VideoTranscript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('video_id', models.CharField(help_text=b'It can be an edx_video_id or an external video id', max_length=255)),
                ('transcript', edxval.models.CustomizableFileField(null=True, blank=True)),
                ('language_code', models.CharField(max_length=50, db_index=True)),
                ('provider', models.CharField(default=b'Custom', max_length=30, choices=[(b'Custom', b'Custom'), (b'3PlayMedia', b'3PlayMedia'), (b'Cielo24', b'Cielo24')])),
                ('file_format', models.CharField(db_index=True, max_length=20, choices=[(b'srt', b'SubRip'), (b'sjson', b'SRT JSON')])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='videotranscript',
            unique_together=set([('video_id', 'language_code')]),
        ),
    ]
