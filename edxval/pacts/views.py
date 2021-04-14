"""
Provider state views needed by pact to setup Provider state for pact verification.
"""
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from edxval.pacts.utils import (
    clear_database,
    setup_successful_video_details_state,
    setup_successful_video_image_state,
    setup_successful_video_status_state,
    setup_successful_video_transcripts_state,
    setup_unsuccessful_video_details_state,
    setup_unsuccessful_video_image_state,
    setup_unsuccessful_video_status_state,
    setup_unsuccessful_video_transcripts_state,
)


@csrf_exempt
@require_POST
def provider_state(request):
    """
    Provider state setup view needed by pact verifier.
    """
    state_setup_mapping = {
        'A valid video_id video exists': setup_successful_video_status_state,
        'A valid video with no details exists': setup_successful_video_details_state,
        'A valid video with no image information exists': setup_successful_video_image_state,
        'A valid video with no video transcript information exists': setup_successful_video_transcripts_state,
        'A valid video and video transcript information exists': setup_unsuccessful_video_transcripts_state,
        'No video and video details exist': setup_unsuccessful_video_details_state,
        'No valid video with video images details exist': setup_unsuccessful_video_image_state,
        'A video against given video id does not exist': setup_unsuccessful_video_status_state,
    }
    request_body = json.loads(request.body)
    state = request_body.get('state')
    if state in state_setup_mapping:
        print('Setting up provider state for state value: {}'.format(state))
        clear_database()
        state_setup_mapping[state]()
    return JsonResponse({'result': state})
