# -*- coding: utf-8 -*-
EDX_VIDEO_ID = "thisis12char-thisis7"

ENCODED_VIDEO_DICT_MOBILE = dict(
    url="http://www.meowmix.com",
    file_size=25556,
    bitrate=9600,
)

ENCODED_VIDEO_DICT_DESKTOP = dict(
    url="http://www.meowmagic.com",
    file_size=25556,
    bitrate=9600,
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
PROFILE_DICT_NON_LATIN = dict(
    profile_name=u"배고파",
    extension="mew",
    width=100,
    height=300
)
VIDEO_DICT_CATS = dict(
    client_video_id="Thunder Cats S01E01",
    duration=111.00,
    edx_video_id="thisis12char-thisis7",
)

VIDEO_DICT_LION = dict(
    client_video_id="Lolcat",
    duration=111.00,
    edx_video_id="caw",
)
VIDEO_DICT_LION2 = dict(
    client_video_id="Lolcat",
    duration=122.00,
    edx_video_id="caw",
)

VIDEO_DICT_TIGERS_BEARS = [
    dict(
        client_video_id="Tipsy Tiger",
        duration=111.00,
        edx_video_id="meeeeeow",
    ),
    dict(
        client_video_id="Boring Bear",
        duration=111.00,
        edx_video_id="hithar",
    )
]

VIDEO_DICT_INVALID_SET = [
    dict(
        client_video_id="Average Animal",
        duration=111.00,
        edx_video_id="mediocrity",
    ),
    dict(
        client_video_id="Barking Bee",
        duration=111.00,
        edx_video_id="wa/sps",
    ),
    dict(
        client_video_id="Callous Coat",
        duration=111.00,
        edx_video_id="not an animal",
    )
]

VIDEO_DICT_DUPLICATES = [
    dict(
        client_video_id="Gaggling gopher",
        duration=111.00,
        edx_video_id="gg",
    ),
    dict(
        client_video_id="Gaggling gopher",
        duration=111.00,
        edx_video_id="gg",
    ),
]

VIDEO_DICT_NEGATIVE_DURATION = dict(
    client_video_id="Thunder Cats S01E01",
    duration=-111,
    edx_video_id="thisis12char-thisis7",
)

VIDEO_DICT_INVALID_ID = dict(
    client_video_id="SuperSloth",
    duration=42,
    edx_video_id="sloppy/sloth!!"
)

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