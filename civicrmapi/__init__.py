"""
About
-----
This package provides a convenient way to access `CiviCRM's API`_ from Python
applications. It supports both API verions `v3`_ and `v4`_ as REST API and via
the console command `cv`_.

.. _CiviCRM's API: https://docs.civicrm.org/dev/en/latest/api/
.. _v3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
.. _v4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/
.. _cv: https://github.com/civicrm/cv


Getting Started
---------------
There are four ready to use api classes:

- :class:`~civicrmapi.rest.RestApiV3` - REST API bindings for CiviCRM APIv3
- :class:`~civicrmapi.rest.RestApiV4` - REST API bindings for CiviCRM APIv4
- :class:`~civicrmapi.console.ConsoleApiV3` - Using `cv` to access CiviCRM APIv3
- :class:`~civicrmapi.console.ConsoleApiV4` - Using `cv` to access CiviCRM APIv4

All you need to do is to initialize the api of your choice and use it::

    >>> api = ConsoleApiV4(cv=cv, context=context)
    >>> params = {
    ...     "contact_type": "Organization",
    ...     "organization_name": "pretty org",
    ...     }
    >>> result = api.Contact.create(params)
    >>> result[0]['organization_name']
    'pretty org'


Concept
-------
There are three main base classes an api binding is built of:

- :class:`~base.BaseApi` - Base class for all API implementations
- :class:`~base.BaseEntity` - Base class for CiviCRM entities
- :class:`~base.BaseAction` - Base class for CiviCRM actions

Initializing an api class will automatically equip it with entities, which
themselves are equipped with actions - each as instance attributes. And on each
level of this hierarchy an api call can be performed. The api, its entities and
their actions are all callable.

The following ways of performing an api call are equivalent::

    >>> api = RestApiV4(url=url, api_key=api_key)
    >>> params = {"contact_type": "Organization"}

    >>> # Calling the action instance.
    >>> result_one = api.Contact.get(params)

    >>> # Calling the entity instance passing the action as parameter.
    >>> result_two = api.Contact('get', params)

    >>> # Calling the api instance  passing the entity and action as parameters.
    >>> result_three = api('Contact', 'get', params)

    >>> result_one == result_two == result_three
    True


The standard entities and actions for each api version are defined within the
the corresponding modules :mod:`~.v3` and :mod:`~.v4`. You can also implement
special behavior like custom validation, result parsing or error handling by
writing your own api, entity or action subclasses.


API Parameters
--------------
The `API v3`_ and `API v4`_ have different formats for api parameters. While the
API v3 uses a flat dictonary with entity field parameters as well as meta
informations like `limit` on the same level, the API v4 has a more structured
and "sql-like" way to format the parameters - using keywords like `select`,
`values`, `where` and `join`.

.. _API v3: https://docs.civicrm.org/dev/en/latest/api/v3/usage/
.. _API v4: https://docs.civicrm.org/dev/en/latest/api/v4/usage/

You can always use the version's specific way of structuring the parameters for
your api call. Just use the `api explorer`_ or read the `api documentation`_ to
check out what's possible and how to achieve it.

.. _api explorer: https://docs.civicrm.org/dev/en/latest/api/#api-explorer
.. _api documentation: https://docs.civicrm.org/dev/en/latest/api/

For simple api calls using only entity field parameters to get, create, delete
or update objects, civicrmapi helps you building the v4 parameters out of a
plain field-value dictonary.

So those Contact.get api calls are equivalent::

    >>> api = ConsoleApiV4(cv=cv, context=context)

    >>> # Api call with original v4 parameter format.:
    >>> params = {
    ...     'where': [
    ...         ['contact_type', '=', 'Individual'],
    ...         ['preferred_language', '=', 'de_DE'],
    ...     ]
    ... }
    >>> result_one = api.Contact.get(params)

    >>> # Api call using a simple field value dictonary:
    >>> params = {
    ...     'contact_type': 'Individual',
    ...     'preferred_language': 'de_DE',
    ... }
    >>> result_two = api.Contact.get(params)

    >>> result_one == result_two
    True



The same works for a create api call::

    >>> api = ConsoleApiV4(cv=cv, context=context)

    >>> # Original v4 parameters are:
    >>> params = {
    ...     'values': {
    ...         'contact_type': 'Organization',
    ...         'organization_name': 'Super Org',
    ...     }
    ... }
    >>> result = api.Contact.create(params)
    >>> result[0]['organization_name']
    'Super Org'

    >>> # Those could be also passed in as:
    >>> params = {
    ...     'contact_type': 'Organization',
    ...     'organization_name': 'Another Super Org',
    ... }
    >>> result = api.Contact.create(params)
    >>> result[0]['organization_name']
    'Another Super Org'


And even for an update api call if you use the id field to select your entity::

    >>> api = ConsoleApiV4(cv=cv, context=context)

    >>> # Original v4 parameters are:
    >>> params = {
    ...     'where': [
    ...         ['id', '=', 1],
    ...     ],
    ...     'values': {
    ...         'organization_name': 'Super Org',
    ...     }
    ... }
    >>> result = api.Contact.update(params)
    >>> result[0]['organization_name']
    'Super Org'

    >>> # Those could be also passed in as:
    >>> params = {
    ...     'id': 1,
    ...     'organization_name': 'Mega Org',
    ... }
    >>> result = api.Contact.update(params)
    >>> result[0]['organization_name']
    'Mega Org'


Results
-------
The REST-API-v3 and v4 as well as the CV-API-v3 returns a dictonary with some
meta data and a values key which holds the result data. Only the CV-API-v4
returns the results as list.

Since the meta data of the result dictonaries are reduntant (such as api
version, action being used, count of the results and other stuff) civicrmapi
skip them and returns for all APIs a plain list of results. So you always get
something like::

    [{'id': 1, ...}, {'id': 2, ...}, ...]


Build your own API class
------------------------
civicrmapi is not only ment as ready-to-use API bindings but also as a build kit
for complex api tasks. New functionality can be implemented on api, entity and
action level. As an example let's build an get-or-create action for the Contact
entity::

    >>> class Contact(BaseEntity):
    ...     NAME = 'Contact'
    ...     def get_or_create(self, params):
    ...         result = self.get(params)
    ...         if not result:
    ...             result = self.create(params)
    ...         return result

    >>> api = ConsoleApiV4(cv=cv, context=context)
    >>> params = {
    ...     'contact_type': 'Organization',
    ...     'organization_name': 'Super Org',
    ... }

    >>> contact_entity = Contact(api)
    >>> contact = contact_entity.get_or_create(params)
    >>> same_contact = contact_entity.get_or_create(params)
    >>> contact[0]['id'] == same_contact[0]['id']
    True

What if we want a get-or-create action for all entities of an api instance?
Let's try another approach using a mixin for our entities::

    >>> class MyMixin:
    ...     def get_or_create(self, params):
    ...         result = self.get(params)
    ...         if not result:
    ...             result = self.create(params)
    ...         return result

    >>> class MyApi(ConsoleApiV4):
    ...     def _add_entities(self):
    ...         for entity in self.VERSION.ENTITIES:
    ...             entity = type(entity, (MyMixin, BaseEntity), dict(NAME=entity))
    ...             setattr(self, entity.NAME, entity(self))

    >>> api = MyApi(cv=cv, context=context)
    >>> params = {
    ...     'contact_id': 2,
    ...     'email': 'foo@bar.de',
    ... }

    >>> email = api.Email.get_or_create(params)
    >>> same_email = api.Email.get_or_create(params)
    >>> email[0]['id'] == same_email[0]['id']
    True

There are surely other options like writing a custom api action and using them
with different entities or writing custom code on an api level to collect
statistics on api usage ect. Use what ever approach fits to your needs.

"""

from .base import BaseAction
from .base import BaseEntity
from .base import BaseApi
from .errors import InvalidApiCall
from .errors import InvalidResponse
from .rest import RestApiV3
from .rest import RestApiV4
from .console import ConsoleApiV3
from .console import ConsoleApiV4