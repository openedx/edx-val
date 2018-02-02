# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


AUDIO_MP3_PROFILE = 'audio_mp3'


def create_audio_mp3_profile(apps, schema_editor):
    """ Create audio_mp3 profile """
    Profile = apps.get_model('edxval', 'Profile')
    Profile.objects.get_or_create(profile_name=AUDIO_MP3_PROFILE)


def delete_audio_mp3_profile(apps, schema_editor):
    """ Delete audio_mp3 profile """
    Profile = apps.get_model('edxval', 'Profile')
    Profile.objects.filter(profile_name=AUDIO_MP3_PROFILE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0010_add_video_as_foreign_key'),
    ]

    operations = [
        migrations.RunPython(create_audio_mp3_profile, delete_audio_mp3_profile),
    ]
