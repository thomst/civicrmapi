import json
import os
import unittest
import logging
import subprocess
import requests
import pprint
import doctest
import civicrmapi
from pathlib import Path
from civicrmapi import __version__
from civicrmapi.errors import InvalidApiCall
from civicrmapi.errors import InvalidResponse
from civicrmapi.base import BaseEntity
from civicrmapi.http import HttpApiV3
from civicrmapi.http import HttpApiV4
from civicrmapi.cv import CvApiV3
from civicrmapi.cv import CvApiV4



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
        self.apis = dict(v3=dict(), v4=dict())
        self.apis['v3']['http'] = HttpApiV3(SETUP['url'], SETUP['api_key'], SETUP['site_key'])
        self.apis['v3']['cv'] = CvApiV3(SETUP['cv'], context=SETUP['context'])
        self.apis['v4']['http'] = HttpApiV4(SETUP['url'], SETUP['api_key'])
        self.apis['v4']['cv'] = CvApiV4(SETUP['cv'], context=SETUP['context'])
        self.apis['all'] = [a for apis in self.apis.values() for a in apis.values()]

    def test_api_initialization(self):
        for api in self.apis['all']:
            for entity in api.VERSION.ENTITIES:
                if isinstance(entity, str):
                    entity_name = entity
                else:
                    entity_name = entity.__name__
                self.assertTrue(hasattr(api, entity_name))
                for action in api.VERSION.ACTIONS:
                    self.assertTrue(hasattr(getattr(api, entity_name), action))

    def test_http_api_with_dummy_url(self):
        api = HttpApiV3('dummy.de', 'FAKE_API_KEY', 'FAKE_SITE_KEY')
        with self.assertRaises(requests.exceptions.RequestException):
            api.Contact.get()
        api = HttpApiV4('dummy.de', 'FAKE_API_KEY')
        with self.assertRaises(requests.exceptions.RequestException):
            api.Contact.get()

    def test_cv_api_with_dummy_cv(self):
        api = CvApiV3('dummy-cv')
        with self.assertRaises(subprocess.CalledProcessError):
            api.Contact.get()
        api = CvApiV4('dummy-cv')
        with self.assertRaises(subprocess.CalledProcessError):
            api.Contact.get()

    def test_cv_with_echo_instead_cv(self):
        api = CvApiV4('echo')
        with self.assertRaises(InvalidResponse):
            api.Contact.get()

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_simple_api_call(self):
        for api in self.apis['all']:
            result = api.Contact.get()
            self.assertIsInstance(result, list)

    def test_create_api_call(self):
        params = {'contact_id': 2, 'email': 'email@example.de'}
        for api in self.apis['v3'].values():
            result = api.Email.create(params)
            self.assertIsInstance(result, list)

        params = {'values': {'contact_id': 2, 'email': 'email@example.de'}}
        for api in self.apis['v4'].values():
            result = api.Email.create(params)
            self.assertIsInstance(result, list)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_compare_api_results(self):
        # Simple api v3 call.
        http_result = self.apis['v3']['http'].Contact.get()
        cv_result = self.apis['v3']['cv'].Contact.get()
        self.assertIsInstance(http_result, list)
        self.assertEqual(len(http_result), len(cv_result))

        # Simple api v4 call.
        http_result = self.apis['v4']['http'].Contact.get()
        cv_result = self.apis['v4']['cv'].Contact.get()
        self.assertIsInstance(http_result, list)
        self.assertEqual(len(http_result), len(cv_result))

        # Use a more complex api v4 call.
        params = dict(
            select=['id', 'contact_type'],
            where=[['contact_type', '=', 'Organization']],
            limit=1
            )
        http_result = self.apis['v4']['http'].Contact.get(params)
        cv_result = self.apis['v4']['cv'].Contact.get(params)
        self.assertIsInstance(http_result, list)
        self.assertEqual(len(http_result), len(cv_result))

        # Use a more complex api v3 call.
        params = {'return': 'id,contact_type', 'contact_type': 'Organization'}
        http_result = self.apis['v3']['http'].Contact.get(params)
        cv_result = self.apis['v3']['cv'].Contact.get(params)
        self.assertIsInstance(http_result, list)
        self.assertEqual(len(http_result), len(cv_result))

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_entity(self):
        for api in self.apis['all']:
            with self.assertRaises(InvalidApiCall):
                api('Foobar', 'get')

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_action(self):
        for api in self.apis['all']:
            with self.assertRaises(InvalidApiCall):
                api.Contact('foobar')

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_field(self):
        # Api v3 and v4 are not consistent in raising errors with invalid field
        # parameters. V3 raises "missing mandatory field" for create, but gives
        # a result list for get. V4 raises "invalid field" error for get, but
        # creates whatever for create.
        params = {'foo': 'bar'}
        for api in self.apis['v3'].values():
            with self.assertRaises(InvalidApiCall):
                api.Contact.create(params)
        for api in self.apis['v4'].values():
            with self.assertRaises(InvalidApiCall):
                api.Contact.get(params)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_invalid_value(self):
        # Api v4 actually creates an email without contact_id for those params.
        # Ups.
        params = {'contact_id': 'not-a-number', 'email': 'not-an-email-address'}
        for api in self.apis['v3'].values():
            with self.assertRaises(InvalidApiCall):
                api.Email.create(params)

    @unittest.skipIf(not SETUP, 'No test installation setup found.')
    def test_api_v4_parameter_preperation(self):
        # Get action with no where key.
        params = {'contact_type': 'Organization'}
        http_result = self.apis['v4']['http'].Contact.get(params)
        cv_result = self.apis['v4']['cv'].Contact.get(params)
        self.assertIsInstance(http_result, list)
        self.assertEqual(http_result, cv_result)
        self.assertEqual(http_result[0]['contact_type'], 'Organization')

        # Create action with no values key.
        params = {'contact_type': 'Organization', 'organization_name': 'Super Org'}
        http_result = self.apis['v4']['http'].Contact.create(params)
        cv_result = self.apis['v4']['cv'].Contact.create(params)
        self.assertIsInstance(http_result, list)
        self.assertIsInstance(cv_result, list)
        self.assertEqual(http_result[0]['organization_name'], 'Super Org')

        # Update action with no where key but an id key.
        contact_id = http_result[0]['id']
        params = {'id': contact_id, 'organization_name': 'Mega Org'}
        http_result = self.apis['v4']['http'].Contact.update(params)
        params = {'id': contact_id, 'organization_name': 'Ultra Org'}
        cv_result = self.apis['v4']['cv'].Contact.update(params)
        self.assertIsInstance(http_result, list)
        self.assertIsInstance(cv_result, list)
        self.assertEqual(cv_result[0]['organization_name'], 'Ultra Org')

        # Delete with no where key.
        params = {'contact_type': 'Organization', 'organization_name': 'Super Org'}
        http_result = self.apis['v4']['http'].Contact.delete(params)
        params = {'contact_type': 'Organization', 'organization_name': 'Ultra Org'}
        cv_result = self.apis['v4']['cv'].Contact.delete(params)
        self.assertIsInstance(http_result, list)
        self.assertIsInstance(cv_result, list)

    def test_docstrings(self):
        globs = dict(
            BaseEntity=BaseEntity,
            CvApiV3=CvApiV3,
            CvApiV4=CvApiV4,
            HttpApiV3=HttpApiV3,
            HttpApiV4=HttpApiV4,
            url=SETUP['url'],
            api_key=SETUP['api_key'],
            cv=SETUP['cv'],
            context=SETUP['context'],
            )
        result = doctest.testmod(civicrmapi, globs=globs)
        self.assertFalse(result.failed)



if __name__ == "__main__":
    unittest.main()
