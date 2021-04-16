### Description

verify_pact.py is the management command for the provider pact verification. It will be used to verify the pacts for which edx-val is the provider.
Since pact provider verification requires a provider url where the interactions will be made, the server should be running before 
executing the management command. Therefore,

1. Run ``python manage.py migrate --settings=edxval.settings.test`` to run the migrations for test database. This will be one-time step for local testing, unless DB structure is changed that will affect Pact verification.
2. Run ``python manage.py runserver --settings=edxval.settings.test`` to start the server against which Pact provider verification will take place.
3. Run ``python manage.py verify_pact --settings=edxval.settings.test`` in another terminal to start the pact verification process.