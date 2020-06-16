# -*- coding: utf-8 -*-


import django.utils.timezone
import edxval.models
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0004_data__add_hls_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('image', edxval.models.CustomizableImageField(null=True, blank=True)),
                ('generated_images', edxval.models.ListField()),
                ('course_video', models.OneToOneField(related_name='video_image', to='edxval.CourseVideo', on_delete = models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
