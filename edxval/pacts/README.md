### Description
This readme contains the description of different files in the current directory.

* middleware.py: This contains an authentication middleware that adds an authenticated user to the requests that are made while running provider verification.
* views.py: This will have provider state setup view which is hit during provider verification to setup appropriate DB state per interaction
* utils.py: Different DB utilities used by views.py
* video-encode-manager-edx-val.json: The only pact file is a duplicate of pact file from https://github.com/edx/video-encode-manager/blob/a4f4c12db0c3919858df1e2fa58ee74071bc264a/encode_manager/apps/core/tests/pact_tests/pacts/video-encode-manager-edx-val.json. This is temporarily needed until pact broker can be setup. Until then, any update in the original pact should be ported in the json in VAL.
* verify_pact.py: Runs the provider verification against the pact. Use either `DJANGO_SETTINGS_MODULE=edxval.settings.pact pytest -s edxval/pacts/verify_pact.py` or `pytest -s edxval/pacts/verify_pact.py --ds=edxval.settings.pact` commands to run the verification.
 There are 3 instances of running the verification:
  * **Verify with broker**: By default, the verification is done against the broker.
  * **Changed Pact's Verification**: For this verification, `VERIFY_WITH_BROKER` environment variable should be set to False and `CHANGED_PACT_URL` should point to a valid pact.
  * **Local JSON Pact**: Similar to Changed Pact Verification. Alternatively, if only `VERIFY_WITH_BROKER` is set to False, the pact named video-encode-manager-edx-val.json will be verified.
  