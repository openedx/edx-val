"""
Provider state views needed by pact to setup Provider state for pact verification.
"""
import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from edxval.pacts.utils import (
    clear_database,
    create_course_video,
    create_video,
    setup_successful_video_details_state,
    setup_unsuccessful_video_transcripts_state,
)

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def provider_state(request):
    """
    Provider state setup view needed by pact verifier.
    """
    state_setup_mapping = {
        'A valid video_id video exists': create_video,
        'A valid video with no details exists': setup_successful_video_details_state,
        'A valid video with no image information exists': create_course_video,
        'A valid video with no video transcript information exists': create_video,
        'A valid video and video transcript information exists': setup_unsuccessful_video_transcripts_state,
    }
    request_body = json.loads(request.body)
    state = request_body.get('state')
    clear_database()
    if state in state_setup_mapping:
        logger.info('Setting up provider state for state value: %s', state)
        state_setup_mapping[state]()
    return JsonResponse({'result': state})
