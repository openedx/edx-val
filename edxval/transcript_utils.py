"""
A module containing transcripts utils.
"""
# pylint: disable=inconsistent-return-statements

from __future__ import absolute_import

import json
import logging

import requests
import six
from django.conf import settings
from pysrt import SubRipFile, SubRipItem, SubRipTime
from pysrt.srtexc import Error
from six import text_type
from six.moves import range

from edxval.exceptions import TranscriptsGenerationException

LOGGER = logging.getLogger(__name__)


class Transcript:
    """
    Container for transcript methods.
    """
    SRT = 'srt'
    SJSON = 'sjson'

    @staticmethod
    def generate_sjson_from_srt(srt_subs):
        """
        Generate transcripts from sjson to SubRip (*.srt).

        Arguments:
            srt_subs(SubRip): "SRT" subs object

        Returns:
            Subs converted to "SJSON" format.
        """
        sub_starts = []
        sub_ends = []
        sub_texts = []
        for sub in srt_subs:
            sub_starts.append(sub.start.ordinal)
            sub_ends.append(sub.end.ordinal)
            sub_texts.append(sub.text.replace('\n', ' '))

        sjson_subs = {
            'start': sub_starts,
            'end': sub_ends,
            'text': sub_texts
        }
        return sjson_subs

    @staticmethod
    def generate_srt_from_sjson(sjson_subs):
        """
        Generate transcripts from sjson to SubRip (*.srt)

        Arguments:
            sjson_subs (dict): `sjson` subs.

        Returns:
            Subtitles in SRT format.
        """
        output = ''

        equal_len = len(sjson_subs['start']) == len(sjson_subs['end']) == len(sjson_subs['text'])
        if not equal_len:
            return output

        for i in range(len(sjson_subs['start'])):
            item = SubRipItem(
                index=i,
                start=SubRipTime(milliseconds=sjson_subs['start'][i]),
                end=SubRipTime(milliseconds=sjson_subs['end'][i]),
                text=sjson_subs['text'][i]
            )
            output += (six.text_type(item))
            output += '\n'
        return output

    @classmethod
    def convert(cls, content, input_format, output_format):
        """
        Convert transcript `content` from `input_format` to `output_format`.

        Arguments:
            content: Transcript content byte-stream.
            input_format: Input transcript format.
            output_format: Output transcript format.

        Accepted input formats: sjson, srt.
        Accepted output format: srt, sjson.

        Raises:
            TranscriptsGenerationException: On parsing the invalid srt
            content during conversion from srt to sjson.
        """
        assert input_format in ('srt', 'sjson')
        assert output_format in ('srt', 'sjson')

        # Decode the content with utf-8-sig which will also
        # skip byte order mark(BOM) character if found.
        content = content.decode('utf-8-sig')

        if input_format == output_format:
            return content

        if input_format == 'srt':

            if output_format == 'sjson':
                try:
                    # With error handling (set to 'ERROR_RAISE'), we will be getting
                    # the exception if something went wrong in parsing the transcript.
                    srt_subs = SubRipFile.from_string(content, error_handling=SubRipFile.ERROR_RAISE)
                except Error as ex:  # Base exception from pysrt
                    raise TranscriptsGenerationException(text_type(ex))

                return json.dumps(cls.generate_sjson_from_srt(srt_subs))

        if input_format == 'sjson':

            if output_format == 'srt':
                return cls.generate_srt_from_sjson(json.loads(content))


def get_cielo_token_response(username, api_secure_key):
    """
    Returns Cielo24 api token.

    Arguments:
        username(str): Cielo24 username
        api_securekey(str): Cielo24 api key

    Returns:
        Response : Http response object
    """
    cielo_api_url = settings.CIELO24_SETTINGS.get('CIELO24_LOGIN_URL', "https://sandbox.cielo24.com/api/account/login")
    return requests.get(cielo_api_url, params={
            'v': settings.CIELO24_SETTINGS.get('CIELO24_API_VERSION', 1),
            'username': username,
            'securekey': api_secure_key
        })


def get_api_token(username, api_key):
    """
    Returns api token if valid credentials are provided.
    """
    response = get_cielo_token_response(username=username, api_secure_key=api_key)
    if not response.ok:
        api_token = None
        LOGGER.warning(
            '[Transcript Credentials] Unable to get api token --  response %s --  status %s.',
            response.text,
            response.status_code,
        )
    else:
        api_token = json.loads(response.content.decode('utf-8'))['ApiToken']

    return api_token
