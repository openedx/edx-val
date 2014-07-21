EV_DICT_CREATE = dict(
    edx_video_id="thisis12char-thisis7_mob",
    url="http://www.meowmix.com",
    file_size=25556,
    bitrate=9600,
)


EV_DICT_UPDATE = dict(
    edx_video_id="thisis12char-thisis7_mob",
    url="http://www.thundercows.com",
    file_size=25556,
    bitrate=9600,
)

P_DICT = dict(
    profile_id="mobile",
    profile_name="mobile thing",
    extension="avi",
    width=100,
    height=101
)

P_DICT2 = dict(
    profile_id="desktop",
    profile_name="desktop thing",
    extension="mp4",
    width=200,
    height=2001
)

V_DICT = dict(
    client_title="Thunder Cats S01E01",
    duration=111,
    video_prefix="thisis12char-thisis7",
)
V_DICT = dict(
    client_title="Lightning Dogs S01E01",
    duration=111,
    video_prefix="thisis12char-dogpoop",
)

edx_id_list = [["thisis12char-thisis7_mob", True],
               ["thisis12char-thisis7", True],
               ["thisis12char-thisis", False],
               ["thisis12char-thisis7_mo", False],
               ["thisis12char-thisis7_mobe", False],
               ["thisis12charlthisis7_mob", False],
               ["thisis12char-thisis7lmob", False],
               ["thisis12charlthisis7lmob", False],
               ["thisis12ch", False],
               ["", False],
               ]