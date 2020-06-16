# -*- coding: utf-8 -*-


from django.db import migrations, models

HLS_PROFILE = 'hls'


def create_hls_profile(apps, schema_editor):
    """ Create hls profile """
    Profile = apps.get_model("edxval", "Profile")
    Profile.objects.get_or_create(profile_name=HLS_PROFILE)


def delete_hls_profile(apps, schema_editor):
    """ Delete hls profile """
    Profile = apps.get_model("edxval", "Profile")
    Profile.objects.filter(profile_name=HLS_PROFILE).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0003_coursevideo_is_hidden'),
    ]

    operations = [
        migrations.RunPython(create_hls_profile, delete_hls_profile),
    ]
