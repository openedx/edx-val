# -*- coding: utf-8 -*-


from django.db import migrations


def copy_column_values(apps, schema_editor):
    """
    Copy the 'exists' field's value into the 'has_creds' field.
    """
    ThirdPartyTranscriptCredentialsState = apps.get_model('edxval', 'ThirdPartyTranscriptCredentialsState')
    for credentials_state in ThirdPartyTranscriptCredentialsState.objects.all():
        credentials_state.has_creds = credentials_state.exists
        credentials_state.save()


class Migration(migrations.Migration):

    dependencies = [
        ('edxval', '0012_thirdpartytranscriptcredentialsstate_has_creds'),
    ]

    operations = [
        migrations.RunPython(
            copy_column_values,
            reverse_code=migrations.RunPython.noop,  # Allow reverse migrations, but make it a no-op.
        ),
    ]
