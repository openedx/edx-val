 # pylint: disable=E1103, W0105
# -*- coding: utf-8 -*-
"""
Constants used for tests.
"""
from edxval.models import (
    TranscriptFormat,
    TranscriptProviderType,
    Cielo24Fidelity,
    Cielo24Turnaround,
    ThreePlayTurnaround
)

EDX_VIDEO_ID = "itchyjacket"
"""
Generic Profiles for manually creating profile objects
"""
PROFILE_MOBILE = "mobile"
PROFILE_DESKTOP = "desktop"
PROFILE_YOUTUBE = "youtube"
PROFILE_HLS = 'hls'
"""
Encoded_videos for test_api, does not have profile.
"""
ENCODED_VIDEO_DICT_MOBILE = dict(
    url="http://www.meowmix.com",
    file_size=11,
    bitrate=22,
)
ENCODED_VIDEO_DICT_DESKTOP = dict(
    url="http://www.meowmagic.com",
    file_size=33,
    bitrate=44,
)
ENCODED_VIDEO_DICT_MOBILE2 = dict(
    url="http://www.woof.com",
    file_size=55,
    bitrate=66,
)
ENCODED_VIDEO_DICT_DESKTOP2 = dict(
    url="http://www.bark.com",
    file_size=77,
    bitrate=88,
)
ENCODED_VIDEO_DICT_MOBILE3 = dict(
    url="http://www.ssss.com",
    file_size=1111,
    bitrate=2222,
)
ENCODED_VIDEO_DICT_DESKTOP3 = dict(
    url="http://www.hiss.com",
    file_size=3333,
    bitrate=4444,
)
ENCODED_VIDEO_DICT_HLS = dict(
    url='https://www.tmnt.com/tmnt101.m3u8',
    file_size=100,
    bitrate=0
)
"""
Validators
"""
VIDEO_DICT_NEGATIVE_DURATION = dict(
    client_video_id="Thunder Cats S01E01",
    duration=-111,
    edx_video_id="thisis12char-thisis7",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
VIDEO_DICT_BEE_INVALID = dict(
    client_video_id="Barking Bee",
    duration=111.00,
    edx_video_id="wa/sps",
    status="test",
)
VIDEO_DICT_INVALID_ID = dict(
    client_video_id="SuperSloth",
    duration=42,
    edx_video_id="sloppy/sloth!!",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
ENCODED_VIDEO_DICT_NEGATIVE_FILESIZE = dict(
    url="http://www.meowmix.com",
    file_size=-25556,
    bitrate=9600,
)
ENCODED_VIDEO_DICT_NEGATIVE_BITRATE = dict(
    url="http://www.meowmix.com",
    file_size=25556,
    bitrate=-9600,
)
"""
Non-latin/invalid
"""
VIDEO_DICT_NON_LATIN_TITLE = dict(
    client_video_id=u"배고픈 햄스터",
    duration=42,
    edx_video_id="ID",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
VIDEO_DICT_NON_LATIN_ID = dict(
    client_video_id="Hungry Hamster",
    duration=42,
    edx_video_id="밥줘",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
PROFILE_INVALID_NAME = "lo/lol"
"""
Subtitles
"""
SUBTITLE_DICT_SRT = dict(
    fmt="srt",
    language="en",
    content="0:0:0\nhello"
)
SUBTITLE_DICT_SJSON = dict(
    fmt="sjson",
    language="fr",
    content='{"start": "00:00:00"}'
)
"""
Fish
"""
VIDEO_DICT_FISH = dict(
    client_video_id="Shallow Swordfish",
    duration=122.00,
    edx_video_id="super-soaker",
    status="test",
)
VIDEO_DICT_FISH_UPDATE = dict(
    client_video_id="Full Swordfish",
    duration=1222.00,
    edx_video_id="super-soaker",
    status="live",
)
VIDEO_DICT_DIFFERENT_ID_FISH = dict(
    client_video_id="Shallow Swordfish",
    duration=122.00,
    edx_video_id="medium-soaker",
    status="test",
)
ENCODED_VIDEO_DICT_FISH_MOBILE = dict(
    url="https://www.swordsingers.com",
    file_size=9000,
    bitrate=42,
    profile="mobile",
)
ENCODED_VIDEO_DICT_FISH_YOUTUBE = dict(
    url="https://www.youtube.com/watch?v=OscRe3pSP80",
    file_size=0,
    bitrate=42,
    profile="youtube",
)
ENCODED_VIDEO_DICT_FISH_DESKTOP = dict(
    url="https://www.swordsplints.com",
    file_size=1234,
    bitrate=4222,
    profile="desktop",
)
ENCODED_VIDEO_DICT_FISH_HLS = dict(
    url='https://www.tmnt.com/tmnt101.m3u8',
    file_size=100,
    bitrate=100,
    profile='hls',
)
ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE = dict(
    url="https://www.fishfellow.com",
    file_size=1,
    bitrate=1,
    profile="mobile",
)
ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP = dict(
    url="https://www.furryfish.com",
    file_size=2,
    bitrate=2,
    profile="desktop",
)
ENCODED_VIDEO_DICT_UPDATE_FISH_HLS = dict(
    url="https://www.comics.com/flash/intro.m3u8",
    file_size=200,
    bitrate=200,
    profile="hls",
)
ENCODED_VIDEO_DICT_FISH_INVALID_PROFILE = dict(
    url="https://www.swordsplints.com",
    file_size=1234,
    bitrate=4222,
    profile="bird"
)
COMPLETE_SET_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP
    ],
    subtitles=[SUBTITLE_DICT_SRT, SUBTITLE_DICT_SJSON],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_FISH_WITH_HLS = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP,
        ENCODED_VIDEO_DICT_FISH_HLS,
    ],
    subtitles=[SUBTITLE_DICT_SRT, SUBTITLE_DICT_SJSON],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_TWO_MOBILE_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_MOBILE
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_UPDATE_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE,
        ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP,
        ENCODED_VIDEO_DICT_UPDATE_FISH_HLS,
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_DIFFERENT_ID_UPDATE_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE,
        ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP
    ],
    subtitles=[SUBTITLE_DICT_SRT, SUBTITLE_DICT_SJSON],
    **VIDEO_DICT_DIFFERENT_ID_FISH
)
COMPLETE_SET_FIRST_HALF_UPDATE_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_UPDATE_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP
    ],
    subtitles=[SUBTITLE_DICT_SRT, SUBTITLE_DICT_SJSON],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_UPDATE_ONLY_DESKTOP_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_UPDATE_FISH_DESKTOP
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_INVALID_PROFILE
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_FISH
)
COMPLETE_SET_INVALID_VIDEO_FISH = dict(
    client_video_id="Shallow Swordfish",
    duration=122.00,
    edx_video_id="super/soaker",
    status="test",
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP
    ],
    subtitles=[SUBTITLE_DICT_SRT]
)

COMPLETE_SETS_ALL_INVALID = [
    COMPLETE_SET_INVALID_VIDEO_FISH,
    COMPLETE_SET_INVALID_VIDEO_FISH
]
"""
Star
"""
VIDEO_DICT_STAR = dict(
    client_video_id="TWINKLE TWINKLE",
    duration=122.00,
    edx_video_id="little-star",
    status="test",
)
ENCODED_VIDEO_DICT_STAR = dict(
    url="https://www.howIwonder.com",
    file_size=9000,
    bitrate=42,
    profile="mobile"
)
ENCODED_VIDEO_UPDATE_DICT_STAR = dict(
    url="https://www.whatyouare.com",
    file_size=9000,
    bitrate=42,
    profile="mobile"
)
COMPLETE_SET_STAR = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_STAR
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_UPDATE_STAR = dict(
    encoded_videos=[
        ENCODED_VIDEO_UPDATE_DICT_STAR
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_WITH_COURSE_KEY = dict(
    courses=['edX/DemoX/Demo_Course'],
    encoded_videos=[
        ENCODED_VIDEO_DICT_STAR
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_WITH_SOME_INVALID_COURSE_KEY = dict(
    courses=[None, False, '', 'edX/DemoX/Astonomy'],
    encoded_videos=[
        ENCODED_VIDEO_DICT_STAR
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_WITH_OTHER_COURSE_KEYS = dict(
    courses=['edX/DemoX/Astonomy', 'edX/DemoX/Zoology'],
    encoded_videos=[
        ENCODED_VIDEO_DICT_STAR
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_NOT_A_LIST = dict(
    encoded_videos=dict(
        url="https://www.howIwonder.com",
        file_size=9000,
        bitrate=42,
        profile=1
    ),
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
COMPLETE_SET_EXTRA_VIDEO_FIELD = dict(
    encoded_videos=[
        dict(
            url="https://www.vulturevideos.com",
            file_size=101010,
            bitrate=1234,
            profile="mobile",
            video="This should be overridden by parent video field"
        )
    ],
    subtitles=[SUBTITLE_DICT_SRT],
    **VIDEO_DICT_STAR
)
"""
Other
"""
VIDEO_DICT_TREE = dict(
    client_video_id="Trees4lyfe",
    duration=532.00,
    edx_video_id="tree-hugger",
    status="test",
)
VIDEO_DICT_PLANT = dict(
    client_video_id="PlantzRule",
    duration=876.00,
    edx_video_id="fernmaster",
    status="test",
)
VIDEO_DICT_ZEBRA = dict(
    client_video_id="Zesty Zebra",
    duration=111.00,
    edx_video_id="zestttt",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
VIDEO_DICT_ANIMAL = dict(
    client_video_id="Average Animal",
    duration=111.00,
    edx_video_id="mediocrity",
    status="test",
    encoded_videos=[],
    subtitles=[]
)
VIDEO_DICT_UPDATE_ANIMAL = dict(
    client_video_id="Above Average Animal",
    duration=999.00,
    edx_video_id="mediocrity",
    status="test",
    encoded_videos=[],
    subtitles=[]
)

VIDEO_TRANSCRIPT_CIELO24 = dict(
    video_id='super-soaker',
    language_code='en',
    transcript='wow.srt',
    provider=TranscriptProviderType.CIELO24,
    file_format=TranscriptFormat.SRT,
)

VIDEO_TRANSCRIPT_3PLAY = dict(
    video_id='super-soaker',
    language_code='de',
    transcript='wow.sjson',
    provider=TranscriptProviderType.THREE_PLAY_MEDIA,
    file_format=TranscriptFormat.SJSON,
)

VIDEO_TRANSCRIPT_CUSTOM = dict(
    video_id='external_video_id',
    language_code='de',
    transcript='wow.srt',
    provider=TranscriptProviderType.CUSTOM,
    file_format=TranscriptFormat.SRT,
)

TRANSCRIPT_PREFERENCES_CIELO24 = dict(
    course_id='edX/DemoX/Demo_Course',
    provider=TranscriptProviderType.CIELO24,
    cielo24_fidelity=Cielo24Fidelity.PROFESSIONAL,
    cielo24_turnaround=Cielo24Turnaround.PRIORITY,
    preferred_languages=['ar'],
    video_source_language='en',
)

TRANSCRIPT_PREFERENCES_3PLAY = dict(
    course_id='edX/DemoX/Demo_Course',
    provider=TranscriptProviderType.THREE_PLAY_MEDIA,
    three_play_turnaround=ThreePlayTurnaround.SAME_DAY_SERVICE,
    preferred_languages=['ar', 'en'],
    video_source_language='en',
)
