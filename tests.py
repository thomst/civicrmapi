import os
import unittest
import logging
from civicrmapi import __version__
from civicrmapi import v3, v4
from civicrmapi.errors import ApiError
from civicrmapi.errors import InvokeError
from civicrmapi.base import BaseApi
from civicrmapi.base import BaseEntity
from civicrmapi.rest import RestApiV3
from civicrmapi.rest import RestApiV4
from civicrmapi.console import ConsoleApiV3
from civicrmapi.console import ConsoleApiV4


URL = os.environ.get('APITEST_URL', None)
API_KEY = os.environ.get('APITEST_API_KEY', None)
SITE_KEY = os.environ.get('APITEST_SITE_KEY', None)
CV = os.environ.get('APITEST_CV', None)
CWD = os.environ.get('APITEST_CWD', None)
CONTEXT = os.environ.get('APITEST_CONTEXT', None)
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



class TestApiConstruction(unittest.TestCase):

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
                self.assertTrue(hasattr(api, entity))
                for action in api.VERSION.ACTIONS:
                    self.assertTrue(hasattr(getattr(api, entity), action))

    def test_entity_initialization(self):
        api = self.base_api_v4()
        # Setup an entity class with a get attribute.
        params = dict(get='fakemethod', newmethod='fakemethod')
        entity_class = type('Contact', (BaseEntity,), params)
        entity = entity_class(api)

        # Check that default actions were added to the entity.
        for action in v4.ACTIONS:
            self.assertTrue(hasattr(entity, action))

        # Check that the get-attribute was not overwritten.
        self.assertEqual(entity.get, 'fakemethod')
        self.assertEqual(entity.newmethod, 'fakemethod')

        # Add our Contact class to the v4 module and check if it will be added
        # to the base-api.
        setattr(v4, 'Contact', entity_class)
        api = self.base_api_v4()
        for action in v4.ACTIONS:
            self.assertTrue(hasattr(api.Contact, action))
        self.assertEqual(api.Contact.get, 'fakemethod')
        self.assertEqual(api.Contact.newmethod, 'fakemethod')
        delattr(v4, 'Contact')

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

    @needs(URL, API_KEY)
    def test_rest_api_v4_call(self):
        api = RestApiV4(URL, API_KEY)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(URL, API_KEY, SITE_KEY)
    def test_rest_api_v3_call(self):
        api = RestApiV3(URL, API_KEY, SITE_KEY)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(CV, CWD)
    def test_console_api_call(self):
        api = ConsoleApiV3(CV, CWD, CONTEXT)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

        api = ConsoleApiV4(CV, CWD, CONTEXT)
        result = api.Contact.get()
        self.assertIsInstance(result, list)

    @needs(URL, API_KEY, SITE_KEY, CV, CWD)
    def test_compare_rest_and_console_results(self):
        api = RestApiV4(URL, API_KEY)
        rest_result = api.Contact.get()
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV4(CV, CWD, CONTEXT)
        console_result = api.Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        params = dict(
            select=['id', 'contact_type'], 
            where=[['contact_type', '=', 'Organization']],
            limit=1
            )
        api = RestApiV4(URL, API_KEY)
        rest_result = api.Contact.get(params)
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV4(CV, CWD, CONTEXT)
        console_result = api.Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        api = RestApiV3(URL, API_KEY, SITE_KEY)
        rest_result = api.Contact.get()
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV3(CV, CWD, CONTEXT)
        console_result = api.Contact.get()
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

        params = {'return': 'id,contact_type', 'contact_type': 'Organization'}
        api = RestApiV3(URL, API_KEY, SITE_KEY)
        rest_result = api.Contact.get(params)
        self.assertIsInstance(rest_result, list)
        api = ConsoleApiV3(CV, CWD, CONTEXT)
        console_result = api.Contact.get(params)
        self.assertIsInstance(console_result, list)
        self.assertEqual(rest_result, console_result)

    @needs(URL, API_KEY, SITE_KEY, CV, CWD)
    def test_invalid_api_calls(self):
        # Invalid api calls.
        api = RestApiV4(URL, API_KEY)
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = RestApiV3(URL, API_KEY, SITE_KEY)
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = ConsoleApiV4(CV, CWD, CONTEXT)
        self.assertRaises(ApiError, api.Contact, 'foobar')
        api = ConsoleApiV3(CV, CWD, CONTEXT)
        self.assertRaises(ApiError, api.Contact, 'foobar')

        # Invalid credentials.
        api = RestApiV4(URL, 'FAKE_API_KEY')
        self.assertRaises(ApiError, api.Contact.get)
        api = RestApiV3(URL, 'FAKE_API_KEY', 'FAKE_SITE_KEY')
        self.assertRaises(ApiError, api.Contact.get)

        # Invalid cv command.
        api = ConsoleApiV4('FAKE_CV', CWD)
        self.assertRaises(ApiError, api.Contact.get)
        api = ConsoleApiV3('FAKE_CV', CWD)
        self.assertRaises(ApiError, api.Contact.get)

    @needs(URL)
    def test_render_api_errors(self):
        try:
            RestApiV4(URL, 'FAKE_API_KEY').Contact.get()
        except ApiError as exc:
            self.assertTrue('HTTP-CODE' in str(exc))
        try:
            RestApiV3(URL, 'FAKE_API_KEY', 'FAKE_SITE_KEY').Contact.get()
        except ApiError as exc:
            self.assertTrue('Invalid credential' in str(exc))
        try:
            ConsoleApiV4(CV, CWD, CONTEXT).Contact('foobar')
        except InvokeError:
            pass
        except ApiError as exc:
            self.assertTrue('version 4 does not exist' in str(exc))
        try:
            ConsoleApiV3(CV, CWD, CONTEXT).Contact('foobar')
        except InvokeError:
            pass
        except ApiError as exc:
            self.assertTrue('not-found' in str(exc))


if __name__ == "__main__":
    unittest.main()
