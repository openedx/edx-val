# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import edxval.models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0004_data__add_hls_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', models.CharField(max_length=255)),
                ('image', edxval.models.CustomizableFileField(null=True, blank=True)),
                ('video', models.ForeignKey(related_name='thumbnails', to='edxval.Video')),
            ],
        ),
    ]
