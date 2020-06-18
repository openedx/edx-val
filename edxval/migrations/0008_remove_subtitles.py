# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0007_transcript_credentials_state'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subtitle',
            name='video',
        ),
        migrations.DeleteModel(
            name='Subtitle',
        ),
    ]
