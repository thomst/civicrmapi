import json
import os
import unittest
import logging
from pathlib import Path
from civicrmapi import __version__
from civicrmapi import v3, v4
from civicrmapi.errors import ApiError
from civicrmapi.errors import SubprocessError
from civicrmapi.base import BaseApi
from civicrmapi.rest import RestApiV3
from civicrmapi.rest import RestApiV4
from civicrmapi.console import ConsoleApiV3
from civicrmapi.console import ConsoleApiV4


# Get directory of this file and build paths to json config files.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TO_CIVICRM_DOCKER = Path(THIS_DIR) / 'civicrm-docker/example/civicrm'
CIVICRM_ADMIN_JSON_FILE = Path(PATH_TO_CIVICRM_DOCKER) / 'civicrm-admin-data.json'
CIVICRM_VARS_JSON_FILE = Path(PATH_TO_CIVICRM_DOCKER) / 'civicrm-vars-data.json'

# Setup some defaults to work with the api of the CiviCRM test installation.
CV = 'cv'
CONTEXT = 'docker-compose exec -T app bash -c'

# Get relevant config data from json files if they exist.
CIVI_CONFIG = dict()
if CIVICRM_ADMIN_JSON_FILE.is_file() and CIVICRM_VARS_JSON_FILE.is_file():
    with open(CIVICRM_ADMIN_JSON_FILE, 'r') as f:
        data = json.load(f)
        CIVI_CONFIG['api_key'] = data[0]['api_key']
    with open(CIVICRM_VARS_JSON_FILE, 'r') as f:
        data = json.load(f)
        CIVI_CONFIG['url'] = data['CMS_URL']
        CIVI_CONFIG['site_key'] = data['CIVI_SITE_KEY']

    # To run cv commands within the docker container we need to jump into the
    # civicrm docker root path.
    os.chdir(PATH_TO_CIVICRM_DOCKER)


# Setup the logger.
LOG_LEVEL = getattr(logging, os.environ.get('APITEST_LOG_LEVEL', 'warning').upper())
logging.basicConfig(level=LOG_LEVEL)


class needs:
    def __init__(self, *params):
        self.params = params

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            if all(self.params):
                return func(*args, **kwargs)
            else:
                return
        return wrapper



class ApiTestCase(unittest.TestCase):

    def setUp(self):
        self.base_api_v3 = type('api', (BaseApi,), dict(VERSION=v3))
        self.base_api_v4 = type('api', (BaseApi,), dict(VERSION=v4))

    def test_api_initialization(self):
        apis = [
            self.base_api_v3(),
            self.base_api_v4(),
            ConsoleApiV3('dummy_cv', 'dummy_cwd'),
            ConsoleApiV4('dummy_cv', 'dummy_cwd'),
            RestApiV3('dummy.de', 'foo', 'bar'),
            RestApiV4('dummy.de', 'foo'),
        ]
        for api in apis:
            for entity in api.VERSION.ENTITIES:
                if isinstance(entity, str):
                    entity_name = entity
                else:
                    entity_name = entity.__name__
                self.assertTrue(hasattr(api, entity_name))
                for action in api.VERSION.ACTIONS:
                    self.assertTrue(hasattr(getattr(api, entity_name), action))

    def test_rest_api_with_dummy_url(self):
        # This could not work.
        api = RestApiV3('dummy.de', 'foo', 'bar')
        self.assertRaises(Exception, api.Contact, 'get', dict())
        api = RestApiV4('dummy.de', 'foo', htaccess={'user': 'foo', 'pass': 'bar'})
        self.assertRaises(Exception, api.Contact.get, dict())

    def test_console_api_with_dummy_cv(self):
        api = ConsoleApiV3('dummy_cv', '/tmp')
        self.assertRaises(Exception, api.Contact.get)
        api = ConsoleApiV4('dummy_cv', 'dummy_cwd')
        self.assertRaises(Exception, api.Contact.get, ['more', 'arguments'])

    @needs(CIVI_CONFIG)
    def test_rest_api_v4_call(self):
        api = RestApiV4(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'])
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(CIVI_CONFIG)
    def test_rest_api_v3_call(self):
        api = RestApiV3(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'], CIVI_CONFIG['site_key'])
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(CIVI_CONFIG)
    def test_console_api_call(self):
        api = ConsoleApiV3(CV, context=CONTEXT)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

        api = ConsoleApiV4(CV, context=CONTEXT)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(CIVI_CONFIG)
    def test_compare_rest_and_console_results(self):
        api = RestApiV4(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'])
        rest_result = api.Contact.get()
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV4(CV, context=CONTEXT)
        console_result = api.Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        params = dict(
            select=['id', 'contact_type'],
            where=[['contact_type', '=', 'Organization']],
            limit=1
            )
        api = RestApiV4(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'])
        rest_result = api.Contact.get(params)
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV4(CV, context=CONTEXT)
        console_result = api.Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        api = RestApiV3(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'], CIVI_CONFIG['site_key'])
        rest_result = api.Contact.get()
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV3(CV, context=CONTEXT)
        console_result = api.Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        params = {'return': 'id,contact_type', 'contact_type': 'Organization'}
        api = RestApiV3(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'], CIVI_CONFIG['site_key'])
        rest_result = api.Contact.get(params)
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV3(CV, context=CONTEXT)
        console_result = api.Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

    @needs(CIVI_CONFIG)
    def test_invalid_api_calls(self):
        # Invalid api calls.
        api = RestApiV4(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'])
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = RestApiV3(CIVI_CONFIG['url'], CIVI_CONFIG['api_key'], CIVI_CONFIG['site_key'])
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = ConsoleApiV4(CV, context=CONTEXT)
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = ConsoleApiV3(CV, context=CONTEXT)
        self.assertRaises(ApiError, api.Contact, 'foobar')

        # Invalid credentials.
        api = RestApiV4(CIVI_CONFIG['url'], 'FAKE_API_KEY')
        self.assertRaises(ApiError, api.Contact.get)
        api = RestApiV3(CIVI_CONFIG['url'], 'FAKE_API_KEY', 'FAKE_SITE_KEY')
        self.assertRaises(ApiError, api.Contact.get)

        # Invalid cv command.
        api = ConsoleApiV4('FAKE_CV', context=CONTEXT)
        self.assertRaises(ApiError, api.Contact.get)
        api = ConsoleApiV3('FAKE_CV', context=CONTEXT)
        self.assertRaises(ApiError, api.Contact.get)

    @needs(CIVI_CONFIG)
    def test_render_api_errors(self):
        try:
            RestApiV4(CIVI_CONFIG['url'], 'FAKE_API_KEY').Contact.get()
        except ApiError as exc:
            self.assertTrue('HTTP-CODE' in str(exc))
        try:
            RestApiV3(CIVI_CONFIG['url'], 'FAKE_API_KEY', 'FAKE_SITE_KEY').Contact.get()
        except ApiError as exc:
            self.assertTrue('Invalid credential' in str(exc))
        try:
            ConsoleApiV4(CV, context=CONTEXT).Contact('foobar')
        except SubprocessError:
            pass
        except ApiError as exc:
            self.assertTrue('version 4 does not exist' in str(exc))
        try:
            ConsoleApiV3(CV, context=CONTEXT).Contact('foobar')
        except SubprocessError:
            pass
        except ApiError as exc:
            self.assertTrue('not-found' in str(exc))


if __name__ == "__main__":
    unittest.main()
