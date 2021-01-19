edx-val (Video Abstraction Layer)
=================================

edx-val is a django app that creates and retrieves metadata for videos and subtitles. When creating video entries, they can be assigned to preset profiles such as 'high_quality' or 'mobile_only'. When requesting a video, the client does not need to know which profile to retrieve, but only the `edx_video_id` of that video. Since all the different profiles for that particular video is returned, the client can decide which profiles they want to use. 
 
Example:
Retrieve all profiles for a video with `edx_video_id`="example"

.. code-block:: python

    >>> get_video_info("example")
    {
        'url' : '/edxval/videos/example',
        'edx_video_id': u'example',
        'duration': 111.0,
        'client_video_id': u'The example video',
        'encoded_videos': [
            {
                'url': u'http://www.example.com/example_mobile_video.mp4',
                'file_size': 25556,
                'bitrate': 9600,
                'profile': u'mobile'
            },
            {
                'url': u'http://www.example.com/example_desktop_video.mp4',
                'file_size': 43096734,
                'bitrate': 64000,
                'profile': u'desktop'
            }
        ]
    }

 
Developing
----------


First, create a virtual environment:

.. code-block:: bash

    virtualenv venvs/val
    source venvs/val/bin/activate

Second, install the necessary reqiurements:

.. code-block:: bash

    make reqiurements

Testing
-------

Both normal testing and CI builds rely on the tox config for testing. 
``tox.inu`` is considered the only source of truth, so it should contain all the Python/Django combinations that need to be tested.

This makes updating the tests in the future really simple, because it would just require updating the ``tox.inu`` file with the latest support python version and specific django releases.
It also provides the freedom for developers to run tests for specific environments with ease. 

Running Tests
~~~~~~~~~~~~~

=================                   ================================================================================
``make quality``                    check coding style with pycodestyle and pylint
``make test``                       run the tox environment tests for the Python version supported in the virtualenv
``make test-all``                   run all the tox environment tests specified in the tox config
=================                   ================================================================================

Tox Tests
~~~~~~~~~

=============================       ================================================================
``tox -e pyNM-djangoNM-unit``       runs all the unit tests for a specific python and django version
``tox -e pyNM-quality``             runs all the quality tests for a specific python version
=============================       ================================================================

Updating Tests
~~~~~~~~~~~~~~

Different updates to the tests should be done in different areas.

The different testing combinations for Python/Django versions should only be updated in tox.

The travis ci config will only specify which specific python versions should be tested with the changes.

~~~~~~~~~
Tox Tests
~~~~~~~~~

Updating the tests will require specifying the Python/Django combination in the ``tox.inu`` file.

The ``[tox]envlist`` and the django ``[django]deps`` should contain all the Python/Django combinations that should be tested for the support Python versions.
Those are the only two fields that would require editting when testing new Python/Django releases.

For example, if testing Python 3.5 with Django 2.2 would require adding the following:

.. code-block:: tox

    [tox]
    envlist =
        py35-django{22}-unit
        py35-quality

    [django]
    deps =
        django22: Django>=2.2,<2.3

Meanwhile, supporting both Python 3.5 with Django 2.2 and Python 3.8 with both Django 2.2 and Django 3.0, would require adding the following instead:

.. code-block:: tox

    [tox]
    envlist =
        py35-django{22}-unit
        py35-quality
        py38-django{22,30}-unit
        py38-quality

    [django]
    deps =
        django22: Django>=2.2,<2.3
        django30: Django>=3.0,<3.1

~~~~~~~~~
Travis CI
~~~~~~~~~

Supporting new python releases in travis ci would only require adding the version to the list of python versions specified in the configuration file:

.. code-block:: yaml

    python:
      - 3.5
      - 3.8
