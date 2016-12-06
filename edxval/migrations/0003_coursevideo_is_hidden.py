# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0002_data__default_profiles'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursevideo',
            name='is_hidden',
            field=models.BooleanField(default=False, help_text=b'Hide video for course.'),
        ),
    ]
