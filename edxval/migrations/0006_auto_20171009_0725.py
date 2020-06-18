# -*- coding: utf-8 -*-


import django.utils.timezone
import edxval.models
import model_utils.fields
from django.db import migrations, models


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
                ('course_id', models.CharField(unique=True, max_length=255, verbose_name=u'Course ID')),
                ('provider', models.CharField(max_length=20, verbose_name=u'Provider', choices=[(u'Custom', u'Custom'), (u'3PlayMedia', u'3PlayMedia'), (u'Cielo24', u'Cielo24')])),
                ('cielo24_fidelity', models.CharField(blank=True, max_length=20, null=True, verbose_name=u'Cielo24 Fidelity', choices=[(u'MECHANICAL', u'Mechanical, 75% Accuracy'), (u'PREMIUM', u'Premium, 95% Accuracy'), (u'PROFESSIONAL', u'Professional, 99% Accuracy')])),
                ('cielo24_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name=u'Cielo24 Turnaround', choices=[(u'STANDARD', u'Standard, 48h'), (u'PRIORITY', u'Priority, 24h')])),
                ('three_play_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name=u'3PlayMedia Turnaround', choices=[(u'extended_service', u'10-Day/Extended'), (u'default', u'4-Day/Default'), (u'expedited_service', u'2-Day/Expedited'), (u'rush_service', u'24 hour/Rush'), (u'same_day_service', u'Same Day')])),
                ('preferred_languages', edxval.models.ListField(default=[], verbose_name=u'Preferred Languages', max_items=50, blank=True)),
                ('video_source_language', models.CharField(help_text=u'This specifies the speech language of a Video.', max_length=50, null=True, verbose_name=u'Video Source Language', blank=True)),
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
                ('video_id', models.CharField(help_text=u'It can be an edx_video_id or an external video id', max_length=255)),
                ('transcript', edxval.models.CustomizableFileField(null=True, blank=True)),
                ('language_code', models.CharField(max_length=50, db_index=True)),
                ('provider', models.CharField(default=u'Custom', max_length=30, choices=[(u'Custom', u'Custom'), (u'3PlayMedia', u'3PlayMedia'), (u'Cielo24', u'Cielo24')])),
                ('file_format', models.CharField(db_index=True, max_length=20, choices=[(u'srt', u'SubRip'), (u'sjson', u'SRT JSON')])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='videotranscript',
            unique_together=set([('video_id', 'language_code')]),
        ),
    ]
