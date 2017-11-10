edx-val (Video Abstraction Layer)
=================================

edx-val is a django app that creates and retrieves metadata for videos and subtitles. When creating video entries, they can be assigned to preset profiles such as 'high_quality' or 'mobile_only'. When requesting a video, the client does not need to know which profile to retrieve, but only the `edx_video_id` of that video. Since all the different profiles for that particular video is returned, the client can decide which profiles they want to use. 
 
Example:
Retrieve all profiles for a video with `edx_video_id`="example"
```
>>> get_video_info("example")
Returns (dict):
{
    'url' : '/edxval/videos/example',
    'edx_video_id': 'example',
    'duration': 111.0,
    'client_video_id': 'The example video',
    'encoded_videos': [
        {
            'url': 'http://www.example.com/example_mobile_video.mp4',
            'file_size': 25556,
            'bitrate': 9600,
            'profile': 'mobile'
        },
        {
            'url': 'http://www.example.com/example_desktop_video.mp4',
            'file_size': 43096734,
            'bitrate': 64000,
            'profile': 'desktop'
        }
    ]
}
```
 
Developing
-----------------
First, create a virtual environment:
```
virtualenv venvs/val
source venvs/val/bin/activate
```

To run tests:
```
pip install -r test-requirements.txt
tox  # to run only a single environment, do e.g. tox -e django18
```
