import unittest
from civicrmapi import __version__
from civicrmapi import v3, v4
from civicrmapi.errors import RestConnectionError
from civicrmapi.errors import RestApiError
from civicrmapi.base import BaseApi
from civicrmapi.base import BaseEntity
from civicrmapi.rest import BaseRestApi
from civicrmapi.rest import RestApiV3
from civicrmapi.rest import RestApiV4


class TestApiConstruction(unittest.TestCase):

    def setUp(self):
        self.url = 'http://fixme.de'
        self.api_key = 'fixme'
        self.site_key = 'fixme'
        self.base_api_v3 = type('api', (BaseApi,), dict(VERSION=v3))
        self.base_api_v4 = type('api', (BaseApi,), dict(VERSION=v4))

    def test_api_initialization(self):
        api = self.base_api_v3()
        self.assertRaises(NotImplementedError, api, 'Entity', 'action', dict())
        for entity in v3.ENTITIES:
            self.assertTrue(hasattr(api, entity))
            for action in v3.ACTIONS:
                self.assertTrue(hasattr(getattr(api, entity), action))

        api = self.base_api_v4()
        for entity in v4.ENTITIES:
            self.assertTrue(hasattr(api, entity))
            for action in v4.ACTIONS:
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
        api = BaseRestApi('dummy.de', htaccess={'user': 'foo', 'pass': 'bar'})
        self.assertRaises(RestConnectionError, api, dict())
        api = RestApiV3('dummy.de', 'foo', 'bar')
        self.assertRaises(RestConnectionError, api.Contact, 'get', dict())
        api = RestApiV4('dummy.de', 'foo')
        self.assertRaises(RestConnectionError, api.Contact.get, dict())