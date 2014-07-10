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
    client_title="Thunder Cats S01E01",
    duration=111.00,
    edx_video_id="thisis12char-thisis7",
)

VIDEO_DICT_NEGATIVE_DURATION = dict(
    client_title="Thunder Cats S01E01",
    duration=-111,
    edx_video_id="thisis12char-thisis7",
)