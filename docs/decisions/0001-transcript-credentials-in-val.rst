Transcript Credentials in VAL
------------------------------

Status
=======
Accepted

Context
========
Transcript credentials are required to submit a transcription job, to a provider, for an user submitted video. They are unique per provider for an organization. The transcription workflow is not possible without these credentials.


Decision
=========
With `VEDA`_, the credentials are located within a VEDA model. However, the other video data lives in VAL. This is a data locality inconsistency even though the credentials are required by VEDA only. With the plans to migrate to `VEM`_ from VEDA, the credentials would not be accessible by VEM if they were in VEDA. Therefore, it was decided to move the existing video transcript credentials from VEDA to VAL. This will bring the credentials in place with related video data. Furthermore, as VAL is accessible by other services(being part of platform), the credentials can be obtained by the services easily.

All the existing credentials have been moved to VAL. However, any updates to credentials will go to VEDA for now. The feature flag for saving credentials in VAL is not active on production at the time of this writing. It will be activated once VEM has replaced VEDA.

.. _VEDA: https://github.com/edx/edx-video-pipeline
.. _VEM: https://github.com/edx/video-encode-manager

Consequences
=============
Moving the credentials in VAL results in a VAL dependency. If VAL is not available, any service seeking transcript credentials will not be successful in its attempt. Therefore, the consumer services must have some fallback option to re-request VAL for credentials if VAL is unavailable.