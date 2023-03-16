import unittest
from civicrmapi import v3, v4
from civicrmapi.base import BaseApi
from civicrmapi.base import BaseEntity
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
        entity_class = type('MyEntity', (BaseEntity,), dict(get='foobar'))
        entity = entity_class(api)

        # Check that default actions were added to the entity.
        for action in v4.ACTIONS:
            self.assertTrue(hasattr(entity, action))

        # Check that the get-attribute was not overwritten.
        self.assertEqual(entity.get, 'foobar')
