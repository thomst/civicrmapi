import json
import os
import unittest
import logging
import subprocess
import requests
import pprint
from pathlib import Path
from civicrmapi import __version__
from civicrmapi.errors import InvalidApiCall
from civicrmapi.errors import InvalidResponse
from civicrmapi.rest import RestApiV3
from civicrmapi.rest import RestApiV4
from civicrmapi.console import ConsoleApiV3
from civicrmapi.console import ConsoleApiV4



# Setup the logger.
LOG_LEVEL = getattr(logging, os.environ.get('APITEST_LOG_LEVEL', 'warning').upper())
logging.basicConfig(level=LOG_LEVEL)

# Setup.
SETUP = dict()

# If at least these environment variable are set we use them as api setup.
if all([v in os.environ for v in ('APITEST_CV', 'APITEST_URL', 'APITEST_API_KEY')]):
    SETUP['cv'] = os.environ.get('APITEST_CV', None)
    SETUP['context'] = os.environ.get('APITEST_CONTEXT', None)
    SETUP['url'] = os.environ.get('APITEST_URL', None)
    SETUP['api_key'] = os.environ.get('APITEST_API_KEY', None)
    SETUP['site_key'] = os.environ.get('APITEST_SITE_KEY', None)

# Otherwise we try our luck with the docker installation.
else:
    # Setup some paths.
    THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    PATH_TO_CIVICRM_DOCKER = Path(THIS_DIR) / 'civicrm-docker/example/civicrm'
    CIVICRM_ADMIN_JSON_FILE = Path(PATH_TO_CIVICRM_DOCKER) / 'civicrm-admin-data.json'
    CIVICRM_VARS_JSON_FILE = Path(PATH_TO_CIVICRM_DOCKER) / 'civicrm-vars-data.json'

    # Use the docker installation if the json data files exists.
    if CIVICRM_ADMIN_JSON_FILE.is_file() and CIVICRM_VARS_JSON_FILE.is_file():
        SETUP['cv'] = 'cv'
        SETUP['context'] = f'docker-compose --project-directory {PATH_TO_CIVICRM_DOCKER} exec -T app bash -c'

        with open(CIVICRM_ADMIN_JSON_FILE, 'r') as f:
            data = json.load(f)
            SETUP['api_key'] = data[0]['api_key']
        with open(CIVICRM_VARS_JSON_FILE, 'r') as f:
            data = json.load(f)
            SETUP['url'] = data['CMS_URL']
            SETUP['site_key'] = data['CIVI_SITE_KEY']


pprint.pprint(SETUP)


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.apis = dict()
        self.apis['rest_v4'] = RestApiV4(SETUP['url'], SETUP['api_key'])
        self.apis['rest_v3'] = RestApiV3(SETUP['url'], SETUP['api_key'], SETUP['site_key'])
        self.apis['cv_v4'] = ConsoleApiV4(SETUP['cv'], context=SETUP['context'])
        self.apis['cv_v3'] = ConsoleApiV3(SETUP['cv'], context=SETUP['context'])

    def test_api_initialization(self):
        for api in self.apis.values():
            for entity in api.VERSION.ENTITIES:
                if isinstance(entity, str):
                    entity_name = entity
                else:
                    entity_name = entity.__name__
                self.assertTrue(hasattr(api, entity_name))
                for action in api.VERSION.ACTIONS:
                    self.assertTrue(hasattr(getattr(api, entity_name), action))

    def test_rest_api_with_dummy_url(self):
        api = RestApiV3('dummy.de', 'FAKE_API_KEY', 'FAKE_SITE_KEY')
        with self.assertRaises(requests.exceptions.RequestException):
            api.Contact.get()
        api = RestApiV4('dummy.de', 'FAKE_API_KEY')
        with self.assertRaises(requests.exceptions.RequestException):
            api.Contact.get()

    def test_console_api_with_dummy_cv(self):
        api = ConsoleApiV3('dummy-cv')
        with self.assertRaises(subprocess.CalledProcessError):
            api.Contact.get()
        api = ConsoleApiV4('dummy-cv')
        with self.assertRaises(subprocess.CalledProcessError):
            api.Contact.get()

    def test_console_with_echo_instead_cv(self):
        api = ConsoleApiV4('echo')
        with self.assertRaises(InvalidResponse):
            api.Contact.get()

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_rest_api_v3_call(self):
        result = self.apis['rest_v3'].Contact.get()
        self.assertIsInstance(result, list)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_rest_api_v4_call(self):
        result = self.apis['rest_v4'].Contact.get()
        self.assertIsInstance(result, list)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_console_api_v3_call(self):
        result = self.apis['cv_v3'].Contact.get()
        self.assertIsInstance(result, list)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_console_api_v4_call(self):
        result = self.apis['cv_v4'].Contact.get()
        self.assertIsInstance(result, list)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_compare_api_results(self):
        # Simple api v3 call.
        rest_result = self.apis['rest_v3'].Contact.get()
        self.assertIsInstance(rest_result, list)
        console_result = self.apis['cv_v3'].Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        # Simple api v4 call.
        rest_result = self.apis['rest_v4'].Contact.get()
        self.assertIsInstance(rest_result, list)
        console_result = self.apis['cv_v4'].Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        # Use a more complex api v4 call.
        params = dict(
            select=['id', 'contact_type'],
            where=[['contact_type', '=', 'Organization']],
            limit=1
            )
        rest_result = self.apis['rest_v4'].Contact.get(params)
        self.assertIsInstance(rest_result, list)
        console_result = self.apis['cv_v4'].Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        # Use a more complex api v3 call.
        params = {'return': 'id,contact_type', 'contact_type': 'Organization'}
        rest_result = self.apis['rest_v3'].Contact.get(params)
        self.assertIsInstance(rest_result, list)
        console_result = self.apis['cv_v3'].Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_entity(self):
        for api in self.apis.values():
            with self.assertRaises(InvalidApiCall):
                api('Foobar', 'get')

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_action(self):
        for api in self.apis.values():
            with self.assertRaises(InvalidApiCall):
                api.Contact('foobar')

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_field(self):
        params = {'foo': 'bar'}
        for api in self.apis.values():
            with self.assertRaises(InvalidApiCall):
                api.Contact.create(params)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_value(self):
        params = {'contact_id': 'not-a-number', 'email': 'not-an-email-address'}
        for api in self.apis.values():
            with self.assertRaises(InvalidApiCall):
                api.Email.create(params)


if __name__ == "__main__":
    unittest.main()
