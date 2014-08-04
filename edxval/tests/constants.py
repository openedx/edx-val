# -*- coding: utf-8 -*-
EDX_VIDEO_ID = "itchyjacket"
"""
Generic Profiles for manually creating profile objects
"""
PROFILE_DICT_MOBILE = dict(
    profile_name="mobile",
    extension="avi",
    width=100,
    height=101
)
PROFILE_DICT_DESKTOP = dict(
    profile_name="desktop",
    extension="mp4",
    width=200,
    height=2001
)
"""
Encoded_videos for test_api, does not have profile.
"""
ENCODED_VIDEO_DICT_MOBILE = dict(
    url="http://www.meowmix.com",
    file_size=4545,
    bitrate=6767,
)

ENCODED_VIDEO_DICT_DESKTOP = dict(
    url="http://www.meowmagic.com",
    file_size=1212,
    bitrate=2323,
)
"""
Validators
"""
VIDEO_DICT_NEGATIVE_DURATION = dict(
    client_video_id="Thunder Cats S01E01",
    duration=-111,
    edx_video_id="thisis12char-thisis7",
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
Non-latin
"""
VIDEO_DICT_NON_LATIN_TITLE = dict(
    client_video_id="배고픈 햄스터",
    duration=42,
    edx_video_id="ID"
)
VIDEO_DICT_NON_LATIN_ID = dict(
    client_video_id="Hungry Hamster",
    duration=42,
    edx_video_id="밥줘"
)
PROFILE_DICT_NON_LATIN = dict(
    profile_name=u"배고파",
    extension="mew",
    width=100,
    height=300
)
"""
Fish
"""
VIDEO_DICT_FISH = dict(
    client_video_id="Shallow Swordfish",
    duration=122.00,
    edx_video_id="supersoaker"
)

ENCODED_VIDEO_DICT_FISH_MOBILE = dict(
    url="https://www.swordsingers.com",
    file_size=9000,
    bitrate=42,
    profile="mobile",
)

ENCODED_VIDEO_DICT_FISH_DESKTOP = dict(
    url="https://www.swordsplints.com",
    file_size=1234,
    bitrate=4222,
    profile="desktop",
)

ENCODED_VIDEO_DICT_FISH_INVALID_PROFILE = dict(
    url="https://www.swordsplints.com",
    file_size=1234,
    bitrate=4222,
    profile=11,
)

COMPLETE_SET_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP
    ],
    **VIDEO_DICT_FISH
)

COMPLETE_SET_INVALID_ENCODED_VIDEO_FISH = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_INVALID_PROFILE
    ],
    **VIDEO_DICT_FISH
)

COMPLETE_SET_INVALID_VIDEO_FISH = dict(
    client_video_id="Shallow Swordfish",
    duration=122.00,
    edx_video_id="super/soaker",
    encoded_videos=[
        ENCODED_VIDEO_DICT_FISH_MOBILE,
        ENCODED_VIDEO_DICT_FISH_DESKTOP
    ]
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
    edx_video_id="little-star"
)
ENCODED_VIDEO_DICT_STAR = dict(
    url="https://www.howIwonder.com",
    file_size=9000,
    bitrate=42,
    profile=1
)
ENCODED_VIDEO_DICT_STAR2 = dict(
    url="https://www.whatyouare.com",
    file_size=1111,
    bitrate=2333,
    profile=2
)

COMPLETE_SET_STAR = dict(
    encoded_videos=[
        ENCODED_VIDEO_DICT_STAR,
        ENCODED_VIDEO_DICT_STAR2
    ],
    **VIDEO_DICT_STAR
)

COMPLETE_SET_NOT_A_LIST = dict(
    encoded_videos=dict(
        url="https://www.howIwonder.com",
        file_size=9000,
        bitrate=42,
        profile=1
    ),
    **VIDEO_DICT_STAR
)

COMPLETE_SET_EXTRA_VIDEO_FIELD = dict(
    encoded_videos=[
        dict(
            url="https://www.vulturevideos.com",
            file_size=101010,
            bitrate=1234,
            profile=1,
            video="This should be overridden by parent videofield"
        )
    ],
    **VIDEO_DICT_STAR
)
"""
Unsorted
"""
VIDEO_DICT_COAT = dict(
    client_video_id="Callous Coat",
    duration=111.00,
    edx_video_id="itchyjacket",
)
VIDEO_DICT_AVERAGE = dict(
    client_video_id="Average Animal",
    duration=111.00,
    edx_video_id="mediocrity",
)
VIDEO_DICT_AVERAGE2 = dict(
    client_video_id="Lolcat",
    duration=122.00,
    edx_video_id="mediocrity",
)

VIDEO_DICT_CRAYFISH = dict(
    client_video_id="Crazy Crayfish",
    duration=111.00,
    edx_video_id="craycray",
)

VIDEO_DICT_BEE_INVALID = dict(
    client_video_id="Barking Bee",
    duration=111.00,
    edx_video_id="wa/sps",
)

VIDEO_DICT_INVALID_ID = dict(
    client_video_id="SuperSloth",
    duration=42,
    edx_video_id="sloppy/sloth!!"
)

VIDEO_DICT_DUPLICATES = [
    VIDEO_DICT_CRAYFISH,
    VIDEO_DICT_CRAYFISH,
    VIDEO_DICT_CRAYFISH
]

COMPLETE_SETS = [
    COMPLETE_SET_STAR,
    COMPLETE_SET_FISH
]

COMPLETE_SETS_ONE_INVALID = [
    COMPLETE_SET_STAR,
    COMPLETE_SET_INVALID_VIDEO_FISH
]

VIDEO_DICT_SET_OF_THREE = [
    VIDEO_DICT_COAT,
    VIDEO_DICT_AVERAGE,
    VIDEO_DICT_CRAYFISH
]

VIDEO_DICT_INVALID_SET = [
    VIDEO_DICT_COAT,
    VIDEO_DICT_INVALID_ID,
    VIDEO_DICT_BEE_INVALID
]