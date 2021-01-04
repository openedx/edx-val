"""
This module contains various configuration settings via
waffle switches for edx's video abstraction layer.
"""


from edx_toggles.toggles.__future__ import WaffleFlag

WAFFLE_NAMESPACE = 'edxval'


def waffle_name(toggle_name):
    """
    Method to append waffle namespace to toggle's name

    Reason behind not using f-strings is backwards compatibility
    Since this is a method, it should be easy to change later on
    """
    return "{namespace}.{toggle_name}".format(
        namespace=WAFFLE_NAMESPACE,
        toggle_name=toggle_name,
    )


# .. toggle_name: OVERRIDE_EXISTING_IMPORTED_TRANSCRIPTS
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
    waffle_name('override_existing_imported_transcripts'),
    module_name=__name__,
)
