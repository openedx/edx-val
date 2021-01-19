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
                ('course_id', models.CharField(unique=True, max_length=255, verbose_name='Course ID')),
                ('provider', models.CharField(max_length=20, verbose_name='Provider', choices=[('Custom', 'Custom'), ('3PlayMedia', '3PlayMedia'), ('Cielo24', 'Cielo24')])),
                ('cielo24_fidelity', models.CharField(blank=True, max_length=20, null=True, verbose_name='Cielo24 Fidelity', choices=[('MECHANICAL', 'Mechanical, 75% Accuracy'), ('PREMIUM', 'Premium, 95% Accuracy'), ('PROFESSIONAL', 'Professional, 99% Accuracy')])),
                ('cielo24_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name='Cielo24 Turnaround', choices=[('STANDARD', 'Standard, 48h'), ('PRIORITY', 'Priority, 24h')])),
                ('three_play_turnaround', models.CharField(blank=True, max_length=20, null=True, verbose_name='3PlayMedia Turnaround', choices=[('extended_service', '10-Day/Extended'), ('default', '4-Day/Default'), ('expedited_service', '2-Day/Expedited'), ('rush_service', '24 hour/Rush'), ('same_day_service', 'Same Day')])),
                ('preferred_languages', edxval.models.ListField(default=[], verbose_name='Preferred Languages', max_items=50, blank=True)),
                ('video_source_language', models.CharField(help_text='This specifies the speech language of a Video.', max_length=50, null=True, verbose_name='Video Source Language', blank=True)),
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
                ('video_id', models.CharField(help_text='It can be an edx_video_id or an external video id', max_length=255)),
                ('transcript', edxval.models.CustomizableFileField(null=True, blank=True)),
                ('language_code', models.CharField(max_length=50, db_index=True)),
                ('provider', models.CharField(default='Custom', max_length=30, choices=[('Custom', 'Custom'), ('3PlayMedia', '3PlayMedia'), ('Cielo24', 'Cielo24')])),
                ('file_format', models.CharField(db_index=True, max_length=20, choices=[('srt', 'SubRip'), ('sjson', 'SRT JSON')])),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='videotranscript',
            unique_together={('video_id', 'language_code')},
        ),
    ]
