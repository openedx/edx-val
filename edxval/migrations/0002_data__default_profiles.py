# -*- coding: utf-8 -*-


from django.db import migrations, models

DEFAULT_PROFILES = [
    "desktop_mp4",
    "desktop_webm",
    "mobile_high",
    "mobile_low",
    "youtube",
]


def create_default_profiles(apps, schema_editor):
    """ Add default profiles """
    Profile = apps.get_model("edxval", "Profile")
    for profile in DEFAULT_PROFILES:
        Profile.objects.get_or_create(profile_name=profile)


def delete_default_profiles(apps, schema_editor):
    """ Remove default profiles """
    Profile = apps.get_model("edxval", "Profile")
    Profile.objects.filter(profile_name__in=DEFAULT_PROFILES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_profiles, delete_default_profiles),
    ]
