"""
This module contains various configuration settings via
waffle switches for edx's video abstraction layer.
"""


from edx_toggles.toggles import WaffleFlag

WAFFLE_NAMESPACE = 'edxval'

# .. toggle_name: edxval.override_existing_imported_transcripts
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables overriding existing transcripts when importing courses with already
#   existing transcripts. The transcripts are compared using content hashing, and if the transcript
#   being imported isn't a duplicate, but different in content, it overrides the existing one.
#   Otherwise, if the transcript is a duplicate, with same content, it doesn't get uploaded.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2021-01-01
# .. toggle_tickets: https://openedx.atlassian.net/browse/OSPR-5117
OVERRIDE_EXISTING_IMPORTED_TRANSCRIPTS = WaffleFlag(
    f'{WAFFLE_NAMESPACE}.override_existing_imported_transcripts', __name__
)
